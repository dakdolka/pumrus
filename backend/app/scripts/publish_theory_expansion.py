"""Publish missing reviewed theory topics without touching manual documents.

The script is a dry run by default.  New topic codes are intentionally used so
that hidden and deprecated records stay intact.  If a visible topic with the
same title already exists, it is treated as manually restored and is skipped.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.infra.catalog.models import ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.scripts.curated_comprehensive_expansion import (
    EXPANSION_REVISION,
    EXPANSION_SOURCES,
    EXPANSION_TOPICS,
)
from app.scripts.publish_curated_theory import _course_version, _publish_document


VISIBLE_TOPIC_STATUSES = ("published", "published_manual")


async def _visible_topic_with_title(
    session: AsyncSession,
    task_id: int,
    title: str,
) -> TopicBD | None:
    return await session.scalar(
        select(TopicBD)
        .join(ExamTaskTopicBD, ExamTaskTopicBD.topic_id == TopicBD.id)
        .where(
            ExamTaskTopicBD.exam_task_id == task_id,
            TopicBD.title == title,
            TopicBD.status.in_(VISIBLE_TOPIC_STATUSES),
        )
        .limit(1)
    )


async def _ensure_topic(
    session: AsyncSession,
    course_version_id: int,
    task: ExamTaskBD,
    definition: dict,
) -> tuple[TopicBD | None, bool]:
    topic = await session.scalar(
        select(TopicBD).where(
            TopicBD.course_version_id == course_version_id,
            TopicBD.code == definition["code"],
        )
    )
    created = topic is None
    if topic is not None:
        # A manual hide/delete is an editorial decision.  Startup publication
        # may release a newer document version, but must never undo it.
        if topic.status not in VISIBLE_TOPIC_STATUSES:
            return None, False
    else:
        visible = await _visible_topic_with_title(session, task.id, definition["title"])
        if visible is not None:
            return None, False
        topic = TopicBD(
            course_version_id=course_version_id,
            code=definition["code"],
            title=definition["title"],
            short_description=definition["description"],
            status="published",
        )
        session.add(topic)
        await session.flush()

    link = await session.get(ExamTaskTopicBD, (task.id, topic.id))
    if link is None:
        max_order = await session.scalar(
            select(func.max(ExamTaskTopicBD.sort_order)).where(
                ExamTaskTopicBD.exam_task_id == task.id
            )
        )
        session.add(ExamTaskTopicBD(
            exam_task_id=task.id,
            topic_id=topic.id,
            sort_order=int(max_order or 0) + 1,
            is_primary=True,
        ))
    return topic, created


async def publish(course_version_code: str | None, execute: bool) -> None:
    async with async_session_factory() as session:
        course_version = await _course_version(session, course_version_code)
        tasks = list((await session.scalars(
            select(ExamTaskBD).where(
                ExamTaskBD.course_version_id == course_version.id
            )
        )).all())
        tasks_by_number = {item.number: item for item in tasks}
        counters = {
            "topics_planned": len(EXPANSION_TOPICS),
            "topics_created": 0,
            "topics_already_visible": 0,
            "documents_published": 0,
            "documents_unchanged": 0,
            "tasks_missing": 0,
        }
        for definition in EXPANSION_TOPICS:
            task = tasks_by_number.get(definition["task_number"])
            if task is None:
                counters["tasks_missing"] += 1
                continue
            topic, created = await _ensure_topic(
                session,
                course_version.id,
                task,
                definition,
            )
            if topic is None:
                counters["topics_already_visible"] += 1
                continue
            counters["topics_created"] += int(created)
            result = await _publish_document(
                session,
                title=definition["title"],
                blocks=definition["blocks"],
                revision=f"{EXPANSION_REVISION}-{definition['code']}",
                sources=EXPANSION_SOURCES,
                topic_id=topic.id,
            )
            counters[f"documents_{result}"] += 1

        print("Comprehensive theory expansion plan:")
        print(f"  course version: {course_version.code}")
        for key, value in counters.items():
            print(f"  {key.replace('_', ' ')}: {value}")
        if execute:
            await session.commit()
            print("Comprehensive theory expansion published successfully.")
        else:
            await session.rollback()
            print("Dry run completed. No theory records were written.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-version")
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    asyncio.run(publish(arguments.course_version, arguments.execute))


if __name__ == "__main__":
    main()
