"""Publish reviewed authorial theory into the v2 content model.

The command is a dry run by default. Use ``--execute`` to write records.
Published versions are preserved; a new version is created only when the
curated revision differs from the currently published one.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.infra.catalog.models import (
    CourseVersionBD,
    ExamTaskBD,
    ExamTaskTopicBD,
    TopicBD,
)
from app.infra.content.models import (
    TheoryBlockV2BD,
    TheoryDocumentBD,
    TheoryDocumentVersionBD,
)
from app.scripts.curated_theory_data import (
    TASK8_INTRO,
    TASK8_REVISION,
    TASK8_SOURCES,
    TASK8_TOPICS,
)


async def _course_version(
    session: AsyncSession,
    code: str | None,
) -> CourseVersionBD:
    query = select(CourseVersionBD)
    if code:
        query = query.where(CourseVersionBD.code == code)
    else:
        query = query.where(CourseVersionBD.is_active.is_(True))
    versions = list((await session.scalars(query)).all())
    if len(versions) != 1:
        target = f"code={code!r}" if code else "the active course version"
        raise RuntimeError(f"Expected exactly one course version for {target}, found {len(versions)}")
    return versions[0]


async def _current_revision(
    session: AsyncSession,
    document: TheoryDocumentBD,
) -> str | None:
    if document.published_version_id is None:
        return None
    return await session.scalar(
        select(TheoryBlockV2BD.settings["curatedRevision"].astext)
        .where(
            TheoryBlockV2BD.document_version_id == document.published_version_id,
            TheoryBlockV2BD.settings["curatedRevision"].astext.is_not(None),
        )
        .limit(1)
    )


async def _publish_document(
    session: AsyncSession,
    *,
    title: str,
    blocks: list[dict[str, Any]],
    revision: str,
    exam_task_id: int | None = None,
    topic_id: int | None = None,
) -> str:
    owner_condition = (
        TheoryDocumentBD.exam_task_id == exam_task_id
        if exam_task_id is not None
        else TheoryDocumentBD.topic_id == topic_id
    )
    document = await session.scalar(select(TheoryDocumentBD).where(owner_condition))
    if document is None:
        document = TheoryDocumentBD(
            exam_task_id=exam_task_id,
            topic_id=topic_id,
            title=title,
            status="published",
        )
        session.add(document)
        await session.flush()
    else:
        document.title = title
    if await _current_revision(session, document) == revision:
        return "unchanged"

    current_number = await session.scalar(
        select(func.max(TheoryDocumentVersionBD.version_number)).where(
            TheoryDocumentVersionBD.document_id == document.id
        )
    )
    now = datetime.now(timezone.utc)
    version = TheoryDocumentVersionBD(
        document_id=document.id,
        version_number=(current_number or 0) + 1,
        status="published",
        published_at=now,
    )
    session.add(version)
    await session.flush()
    for order, block in enumerate(blocks):
        session.add(
            TheoryBlockV2BD(
                document_version_id=version.id,
                block_type=block["type"],
                schema_version=1,
                data=block["data"],
                settings={
                    **block.get("settings", {}),
                    "curatedRevision": revision,
                    "sources": TASK8_SOURCES,
                },
                sort_order=order,
            )
        )
    document.status = "published"
    document.published_version_id = version.id
    return "published"


async def publish_task8(
    session: AsyncSession,
    course_version: CourseVersionBD,
) -> dict[str, int]:
    task = await session.scalar(
        select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == course_version.id,
            ExamTaskBD.number == 8,
        )
    )
    if task is None:
        raise RuntimeError("Task 8 does not exist in the selected course version")
    task.title = TASK8_INTRO["title"]
    task.short_description = TASK8_INTRO["short_description"]
    task.status = "published"

    counters = {"topics_created": 0, "documents_published": 0, "documents_unchanged": 0}
    result = await _publish_document(
        session,
        title=TASK8_INTRO["document_title"],
        blocks=TASK8_INTRO["blocks"],
        revision=TASK8_REVISION,
        exam_task_id=task.id,
    )
    counters[f"documents_{result}"] += 1

    for order, definition in enumerate(TASK8_TOPICS):
        topic = await session.scalar(
            select(TopicBD).where(
                TopicBD.course_version_id == course_version.id,
                TopicBD.code == definition["code"],
            )
        )
        if topic is None:
            topic = TopicBD(
                course_version_id=course_version.id,
                code=definition["code"],
                title=definition["title"],
                short_description=definition["description"],
                status="published",
            )
            session.add(topic)
            await session.flush()
            counters["topics_created"] += 1
        else:
            topic.title = definition["title"]
            topic.short_description = definition["description"]
            topic.status = "published"

        link = await session.get(ExamTaskTopicBD, (task.id, topic.id))
        if link is None:
            link = ExamTaskTopicBD(
                exam_task_id=task.id,
                topic_id=topic.id,
                sort_order=order,
                is_primary=True,
            )
            session.add(link)
        else:
            link.sort_order = order
            link.is_primary = True

        result = await _publish_document(
            session,
            title=definition["title"],
            blocks=definition["blocks"],
            revision=TASK8_REVISION,
            topic_id=topic.id,
        )
        counters[f"documents_{result}"] += 1
    return counters


async def run(course_version_code: str | None, execute: bool) -> None:
    async with async_session_factory() as session:
        version = await _course_version(session, course_version_code)
        counters = await publish_task8(session, version)
        print("Curated theory publication plan:")
        print(f"  course version: {version.code}")
        print(f"  revision: {TASK8_REVISION}")
        print(f"  topics to create: {counters['topics_created']}")
        print(f"  documents to publish: {counters['documents_published']}")
        print(f"  documents already current: {counters['documents_unchanged']}")
        if execute:
            await session.commit()
            print("Task 8 theory published successfully.")
        else:
            await session.rollback()
            print("Dry run completed. No records were written. Use --execute to publish.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-version", default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.course_version, args.execute))


if __name__ == "__main__":
    main()

