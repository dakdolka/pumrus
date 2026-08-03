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
from app.scripts.curated_theory_remaining import BUNDLES


OBSOLETE_BASELINE_TASKS = {2, 4, 5, 6}
OBSOLETE_BASELINE_TOPIC_CODES = {
    "task-2-context",
    "task-4-stress",
    "task-5-paronyms",
    "task-6-lexical",
}


async def _course_version(
    session: AsyncSession,
    code: str | None,
) -> CourseVersionBD:
    if code:
        versions = list(
            (await session.scalars(select(CourseVersionBD).where(CourseVersionBD.code == code))).all()
        )
        if len(versions) != 1:
            raise RuntimeError(f"Expected exactly one course version for code={code!r}, found {len(versions)}")
        return versions[0]

    ranked = list(
        (
            await session.execute(
                select(CourseVersionBD, func.count(ExamTaskBD.id).label("task_count"))
                .outerjoin(ExamTaskBD, ExamTaskBD.course_version_id == CourseVersionBD.id)
                .group_by(CourseVersionBD.id)
                .order_by(func.count(ExamTaskBD.id).desc(), CourseVersionBD.is_active.desc())
            )
        ).all()
    )
    if not ranked:
        raise RuntimeError("No course versions exist")
    best_count = ranked[0].task_count
    best = [row for row in ranked if row.task_count == best_count]
    if len(best) > 1 and not any(row.CourseVersionBD.is_active for row in best):
        raise RuntimeError(
            "Several equally complete course versions exist; pass --course-version explicitly"
        )
    return next(
        (row.CourseVersionBD for row in best if row.CourseVersionBD.is_active),
        best[0].CourseVersionBD,
    )


async def _has_revision(
    session: AsyncSession,
    document: TheoryDocumentBD,
    revision: str,
) -> bool:
    found_revision = await session.scalar(
        select(TheoryBlockV2BD.settings["curatedRevision"].astext)
        .join(
            TheoryDocumentVersionBD,
            TheoryDocumentVersionBD.id == TheoryBlockV2BD.document_version_id,
        )
        .where(
            TheoryDocumentVersionBD.document_id == document.id,
            TheoryBlockV2BD.settings["curatedRevision"].astext == revision,
        )
        .limit(1)
    )
    return found_revision is not None


async def _publish_document(
    session: AsyncSession,
    *,
    title: str,
    blocks: list[dict[str, Any]],
    revision: str,
    sources: list[str],
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
    if await _has_revision(session, document, revision):
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
                    "sources": sources,
                },
                sort_order=order,
            )
        )
    document.status = "published"
    document.published_version_id = version.id
    return "published"


async def _version_revision(
    session: AsyncSession,
    version_id: int | None,
) -> str | None:
    if version_id is None:
        return None
    return await session.scalar(
        select(TheoryBlockV2BD.settings["curatedRevision"].astext)
        .where(TheoryBlockV2BD.document_version_id == version_id)
        .limit(1)
    )


async def _restore_before_baseline(
    session: AsyncSession,
    document: TheoryDocumentBD | None,
) -> bool:
    if document is None or not (await _version_revision(session, document.published_version_id) or "").startswith(
        "ege-2026-baseline-v1-"
    ):
        return False
    previous_versions = list(
        (
            await session.scalars(
                select(TheoryDocumentVersionBD)
                .where(
                    TheoryDocumentVersionBD.document_id == document.id,
                    TheoryDocumentVersionBD.id != document.published_version_id,
                    TheoryDocumentVersionBD.status == "published",
                )
                .order_by(TheoryDocumentVersionBD.version_number.desc())
            )
        ).all()
    )
    previous = None
    for candidate in previous_versions:
        candidate_revision = await _version_revision(session, candidate.id)
        if not (candidate_revision or "").startswith("ege-2026-baseline-v1-"):
            previous = candidate
            break
    document.published_version_id = previous.id if previous else None
    document.status = "published" if previous else "draft"
    return True


async def remove_obsolete_baseline(
    session: AsyncSession,
    course_version: CourseVersionBD,
) -> int:
    restored = 0
    for number in OBSOLETE_BASELINE_TASKS:
        task = await session.scalar(
            select(ExamTaskBD).where(
                ExamTaskBD.course_version_id == course_version.id,
                ExamTaskBD.number == number,
            )
        )
        if task is None:
            continue
        document = await session.scalar(
            select(TheoryDocumentBD).where(TheoryDocumentBD.exam_task_id == task.id)
        )
        restored += int(await _restore_before_baseline(session, document))

    for code in OBSOLETE_BASELINE_TOPIC_CODES:
        topic = await session.scalar(
            select(TopicBD).where(
                TopicBD.course_version_id == course_version.id,
                TopicBD.code == code,
            )
        )
        if topic is None:
            continue
        document = await session.scalar(
            select(TheoryDocumentBD).where(TheoryDocumentBD.topic_id == topic.id)
        )
        was_restored = await _restore_before_baseline(session, document)
        restored += int(was_restored)
        if was_restored and document is not None and document.published_version_id is None:
            topic.status = "draft"
    return restored


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
        return {
            "tasks_skipped": 1,
            "topics_created": 0,
            "documents_published": 0,
            "documents_unchanged": 0,
        }
    task.title = TASK8_INTRO["title"]
    task.short_description = TASK8_INTRO["short_description"]
    task.status = "published"

    counters = {
        "tasks_skipped": 0,
        "topics_created": 0,
        "documents_published": 0,
        "documents_unchanged": 0,
    }
    result = await _publish_document(
        session,
        title=TASK8_INTRO["document_title"],
        blocks=TASK8_INTRO["blocks"],
        revision=TASK8_REVISION,
        sources=TASK8_SOURCES,
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
            sources=TASK8_SOURCES,
            topic_id=topic.id,
        )
        counters[f"documents_{result}"] += 1
    return counters


async def publish_bundle(
    session: AsyncSession,
    course_version: CourseVersionBD,
    definition: dict[str, Any],
) -> dict[str, int]:
    task = await session.scalar(
        select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == course_version.id,
            ExamTaskBD.number == definition["number"],
        )
    )
    counters = {
        "tasks_skipped": 0,
        "topics_created": 0,
        "documents_published": 0,
        "documents_unchanged": 0,
    }
    if task is None:
        counters["tasks_skipped"] = 1
        return counters

    task.title = definition["title"]
    task.short_description = definition["short_description"]
    task.status = "published"
    result = await _publish_document(
        session,
        title=definition["document_title"],
        blocks=definition["blocks"],
        revision=definition["revision"],
        sources=definition["sources"],
        exam_task_id=task.id,
    )
    counters[f"documents_{result}"] += 1

    for order, topic_definition in enumerate(definition["topics"]):
        topic_record = await session.scalar(
            select(TopicBD).where(
                TopicBD.course_version_id == course_version.id,
                TopicBD.code == topic_definition["code"],
            )
        )
        if topic_record is None:
            topic_record = TopicBD(
                course_version_id=course_version.id,
                code=topic_definition["code"],
                title=topic_definition["title"],
                short_description=topic_definition["description"],
                status="published",
            )
            session.add(topic_record)
            await session.flush()
            counters["topics_created"] += 1
        else:
            topic_record.title = topic_definition["title"]
            topic_record.short_description = topic_definition["description"]
            topic_record.status = "published"

        link = await session.get(ExamTaskTopicBD, (task.id, topic_record.id))
        if link is None:
            session.add(ExamTaskTopicBD(
                exam_task_id=task.id,
                topic_id=topic_record.id,
                sort_order=order,
                is_primary=True,
            ))
        else:
            link.sort_order = order
            link.is_primary = True

        result = await _publish_document(
            session,
            title=topic_definition["title"],
            blocks=topic_definition["blocks"],
            revision=definition["revision"],
            sources=definition["sources"],
            topic_id=topic_record.id,
        )
        counters[f"documents_{result}"] += 1
    return counters


async def run(course_version_code: str | None, execute: bool) -> None:
    async with async_session_factory() as session:
        version = await _course_version(session, course_version_code)
        obsolete_restored = await remove_obsolete_baseline(session, version)
        results = [await publish_task8(session, version)]
        for bundle in BUNDLES:
            results.append(await publish_bundle(session, version, bundle))
        counters = {
            key: sum(result.get(key, 0) for result in results)
            for key in ("tasks_skipped", "topics_created", "documents_published", "documents_unchanged")
        }
        print("Curated theory publication plan:")
        print(f"  course version: {version.code}")
        print(f"  bundles: {len(BUNDLES) + 1}")
        print(f"  obsolete baseline documents restored/hidden: {obsolete_restored}")
        print(f"  tasks skipped because absent: {counters['tasks_skipped']}")
        print(f"  topics to create: {counters['topics_created']}")
        print(f"  documents to publish: {counters['documents_published']}")
        print(f"  documents already current: {counters['documents_unchanged']}")
        if execute:
            await session.commit()
            print("Curated theory published successfully.")
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
