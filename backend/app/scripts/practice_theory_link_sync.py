"""Publish missing links from current theory documents to practice scopes."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.catalog.models import ExamTaskBD, TopicBD
from app.infra.content.models import (
    TheoryBlockV2BD,
    TheoryDocumentBD,
    TheoryDocumentVersionBD,
)
from app.infra.exercises.models import ExerciseSetBD


LINK_REVISION = "practice-theory-links-2026-v1"


def _is_matching_link(
    block: TheoryBlockV2BD,
    *,
    exercise_set_id: int,
    task_number: int,
    scope_role: str,
) -> bool:
    if block.block_type != "practice_link":
        return False
    data = block.data or {}
    if int(data.get("exerciseSetId") or 0) == exercise_set_id:
        return True
    return (
        scope_role == "task"
        and not data.get("exerciseSetId")
        and int(data.get("taskNumber") or 0) == task_number
    )


async def _publish_linked_version(
    session: AsyncSession,
    *,
    document: TheoryDocumentBD,
    blocks: list[TheoryBlockV2BD],
    exercise_set: ExerciseSetBD,
    task_number: int,
    topic_title: str | None,
) -> None:
    next_version = int(await session.scalar(
        select(func.coalesce(func.max(TheoryDocumentVersionBD.version_number), 0))
        .where(TheoryDocumentVersionBD.document_id == document.id)
    )) + 1
    now = datetime.now(timezone.utc)
    version = TheoryDocumentVersionBD(
        document_id=document.id,
        version_number=next_version,
        status="published",
        published_at=now,
    )
    session.add(version)
    await session.flush()

    clones: dict[int, TheoryBlockV2BD] = {}
    for source in blocks:
        clone = TheoryBlockV2BD(
            document_version_id=version.id,
            parent_block_id=None,
            block_type=source.block_type,
            schema_version=source.schema_version,
            data=deepcopy(source.data or {}),
            settings=deepcopy(source.settings or {}),
            sort_order=source.sort_order,
        )
        session.add(clone)
        clones[source.id] = clone
    await session.flush()
    for source in blocks:
        if source.parent_block_id in clones:
            clones[source.id].parent_block_id = clones[source.parent_block_id].id

    scope_role = (exercise_set.configuration or {}).get("scopeRole")
    is_topic = scope_role == "topic"
    markdown = (
        "**Проверь правило на практике.** Здесь собраны упражнения только "
        f"по теме «{topic_title}», поэтому её можно отработать отдельно."
        if is_topic
        else "**Закрепи задание целиком.** В смешанном тренажёре собраны "
        "упражнения по всем доступным темам — они будут чередоваться."
    )
    root_order = max(
        (block.sort_order for block in blocks if block.parent_block_id is None),
        default=-1,
    ) + 1
    session.add(TheoryBlockV2BD(
        document_version_id=version.id,
        parent_block_id=None,
        block_type="practice_link",
        schema_version=1,
        data={
            "markdown": markdown,
            "taskNumber": task_number,
            "exerciseSetId": exercise_set.id,
            "buttonLabel": (
                "Отработать эту тему"
                if is_topic
                else "Практика по всему заданию"
            ),
        },
        settings={"generatedBy": LINK_REVISION},
        sort_order=root_order,
    ))
    document.published_version_id = version.id
    document.status = "published"


async def sync_practice_theory_links(
    session: AsyncSession,
    course_version_id: int,
) -> dict[str, int]:
    stats = {
        "theory_practice_links_published": 0,
        "theory_practice_links_existing": 0,
        "theory_practice_links_skipped": 0,
    }
    scopes = (await session.execute(
        select(ExerciseSetBD, ExamTaskBD.number, TopicBD.title)
        .join(ExamTaskBD, ExamTaskBD.id == ExerciseSetBD.exam_task_id)
        .outerjoin(TopicBD, TopicBD.id == ExerciseSetBD.topic_id)
        .where(
            ExerciseSetBD.course_version_id == course_version_id,
            ExerciseSetBD.status == "published",
            ExerciseSetBD.configuration["scopeRole"].astext.in_(("task", "topic")),
        )
        .order_by(ExamTaskBD.number, ExerciseSetBD.topic_id)
    )).all()

    for exercise_set, task_number, topic_title in scopes:
        scope_role = (exercise_set.configuration or {}).get("scopeRole")
        owner_condition = (
            TheoryDocumentBD.topic_id == exercise_set.topic_id
            if scope_role == "topic"
            else TheoryDocumentBD.exam_task_id == exercise_set.exam_task_id
        )
        document = await session.scalar(
            select(TheoryDocumentBD).where(
                owner_condition,
                TheoryDocumentBD.published_version_id.is_not(None),
            )
        )
        if document is None:
            stats["theory_practice_links_skipped"] += 1
            continue
        blocks = list((await session.scalars(
            select(TheoryBlockV2BD)
            .where(
                TheoryBlockV2BD.document_version_id
                == document.published_version_id
            )
            .order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id)
        )).all())
        if any(
            _is_matching_link(
                block,
                exercise_set_id=exercise_set.id,
                task_number=task_number,
                scope_role=scope_role,
            )
            for block in blocks
        ):
            stats["theory_practice_links_existing"] += 1
            continue
        await _publish_linked_version(
            session,
            document=document,
            blocks=blocks,
            exercise_set=exercise_set,
            task_number=task_number,
            topic_title=topic_title,
        )
        stats["theory_practice_links_published"] += 1

    await session.flush()
    return stats
