from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
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
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
)
from app.infra.practice.models import (
    AttemptV2BD,
    PracticeSessionBD,
    PracticeSessionItemBD,
)


router = APIRouter(prefix="/v2", tags=["v2"])
VISIBLE_TOPIC_STATUSES = ("published", "published_manual")


class SessionCreateIn(BaseModel):
    exercise_set_id: int
    user_id: int | None = None
    client_session_id: str | None = Field(default=None, min_length=8, max_length=128)
    mode: str = "standard"
    limit: int | None = Field(default=None, ge=1, le=100)
    page_size: int | None = Field(default=None, ge=1, le=20)


class AnswerIn(BaseModel):
    response: dict[str, Any]


def _task_out(task: ExamTaskBD, topic_count: int = 0) -> dict[str, Any]:
    return {
        "id": task.id,
        "number": task.number,
        "code": task.code,
        "title": task.title,
        "shortDescription": task.short_description,
        "topicCount": topic_count,
    }


def _topic_out(topic: TopicBD) -> dict[str, Any]:
    return {
        "id": topic.id,
        "code": topic.code,
        "title": topic.title,
        "shortDescription": topic.short_description,
    }


def _block_out(
    block: TheoryBlockV2BD,
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = {
        "id": block.id,
        "parentId": block.parent_block_id,
        "type": block.block_type,
        "schemaVersion": block.schema_version,
        "data": block.data,
        "settings": block.settings,
        "sortOrder": block.sort_order,
    }
    if children is not None:
        result["children"] = children
    return result


def _block_tree(blocks: list[TheoryBlockV2BD]) -> list[dict[str, Any]]:
    by_parent: dict[int | None, list[TheoryBlockV2BD]] = {}
    block_ids = {block.id for block in blocks}
    for block in blocks:
        parent_id = (
            block.parent_block_id
            if block.parent_block_id in block_ids
            else None
        )
        by_parent.setdefault(parent_id, []).append(block)

    for siblings in by_parent.values():
        siblings.sort(key=lambda block: (block.sort_order, block.id))

    def serialize(block: TheoryBlockV2BD, ancestors: frozenset[int]) -> dict[str, Any]:
        if block.id in ancestors:
            return _block_out(block, [])
        next_ancestors = ancestors | {block.id}
        return _block_out(
            block,
            [
                serialize(child, next_ancestors)
                for child in by_parent.get(block.id, [])
            ],
        )

    return [serialize(block, frozenset()) for block in by_parent.get(None, [])]


async def _published_document(
    db: AsyncSession,
    *,
    exam_task_id: int | None = None,
    topic_id: int | None = None,
) -> dict[str, Any] | None:
    conditions = [TheoryDocumentBD.status == "published"]
    if exam_task_id is not None:
        conditions.append(TheoryDocumentBD.exam_task_id == exam_task_id)
    if topic_id is not None:
        conditions.append(TheoryDocumentBD.topic_id == topic_id)
    document = await db.scalar(select(TheoryDocumentBD).where(*conditions))
    if document is None or document.published_version_id is None:
        return None
    version = await db.scalar(
        select(TheoryDocumentVersionBD).where(
            TheoryDocumentVersionBD.id == document.published_version_id,
            TheoryDocumentVersionBD.status == "published",
        )
    )
    if version is None:
        return None
    blocks = (
        await db.scalars(
            select(TheoryBlockV2BD)
            .where(TheoryBlockV2BD.document_version_id == version.id)
            .order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id)
        )
    ).all()
    return {
        "id": document.id,
        "title": document.title,
        "version": version.version_number,
        "blocks": _block_tree(list(blocks)),
    }


@router.get("/catalog/tasks")
async def list_exam_tasks(
    mode: Literal["theory", "practice"] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    topic_count = (
        select(func.count(ExamTaskTopicBD.topic_id))
        .join(TopicBD, TopicBD.id == ExamTaskTopicBD.topic_id)
        .where(
            ExamTaskTopicBD.exam_task_id == ExamTaskBD.id,
            TopicBD.status.in_(VISIBLE_TOPIC_STATUSES),
        )
        .correlate(ExamTaskBD)
        .scalar_subquery()
    )
    theory_block_count = (
        select(func.count(TheoryBlockV2BD.id))
        .join(
            TheoryDocumentVersionBD,
            TheoryDocumentVersionBD.id == TheoryBlockV2BD.document_version_id,
        )
        .join(
            TheoryDocumentBD,
            TheoryDocumentBD.id == TheoryDocumentVersionBD.document_id,
        )
        .join(
            ExamTaskTopicBD,
            ExamTaskTopicBD.topic_id == TheoryDocumentBD.topic_id,
        )
        .where(
            ExamTaskTopicBD.exam_task_id == ExamTaskBD.id,
            TheoryDocumentBD.status == "published",
            TheoryDocumentBD.published_version_id == TheoryDocumentVersionBD.id,
            TheoryDocumentVersionBD.status == "published",
        )
        .correlate(ExamTaskBD)
        .scalar_subquery()
    )
    exercise_count = (
        select(func.count(ExerciseSetItemBD.id))
        .join(
            ExerciseSetBD,
            ExerciseSetBD.id == ExerciseSetItemBD.exercise_set_id,
        )
        .join(ExerciseBD, ExerciseBD.id == ExerciseSetItemBD.exercise_id)
        .where(
            ExerciseSetBD.exam_task_id == ExamTaskBD.id,
            ExerciseSetBD.status == "published",
            ExerciseBD.status == "published",
            ExerciseBD.published_version_id.is_not(None),
        )
        .correlate(ExamTaskBD)
        .scalar_subquery()
    )
    exercise_set_count = (
        select(func.count(func.distinct(ExerciseSetBD.id)))
        .join(
            ExerciseSetItemBD,
            ExerciseSetItemBD.exercise_set_id == ExerciseSetBD.id,
        )
        .join(ExerciseBD, ExerciseBD.id == ExerciseSetItemBD.exercise_id)
        .where(
            ExerciseSetBD.exam_task_id == ExamTaskBD.id,
            ExerciseSetBD.status == "published",
            ExerciseBD.status == "published",
            ExerciseBD.published_version_id.is_not(None),
        )
        .correlate(ExamTaskBD)
        .scalar_subquery()
    )
    direct_exercise_set_id = (
        select(func.min(ExerciseSetBD.id))
        .join(
            ExerciseSetItemBD,
            ExerciseSetItemBD.exercise_set_id == ExerciseSetBD.id,
        )
        .join(ExerciseBD, ExerciseBD.id == ExerciseSetItemBD.exercise_id)
        .where(
            ExerciseSetBD.exam_task_id == ExamTaskBD.id,
            ExerciseSetBD.status == "published",
            ExerciseBD.status == "published",
            ExerciseBD.published_version_id.is_not(None),
        )
        .correlate(ExamTaskBD)
        .scalar_subquery()
    )
    conditions = [
        ExamTaskBD.status == "published",
        CourseVersionBD.is_active.is_(True),
    ]
    if mode == "theory":
        conditions.extend((topic_count > 0, theory_block_count > 0))
    elif mode == "practice":
        conditions.append(exercise_count > 0)
    rows = (
        await db.execute(
            select(
                ExamTaskBD,
                topic_count.label("topic_count"),
                exercise_set_count.label("exercise_set_count"),
                direct_exercise_set_id.label("direct_exercise_set_id"),
            )
            .join(
                CourseVersionBD,
                CourseVersionBD.id == ExamTaskBD.course_version_id,
            )
            .where(*conditions)
            .order_by(ExamTaskBD.sort_order, ExamTaskBD.number)
        )
    ).all()
    return [
        {
            **_task_out(task, topic_count),
            "exerciseSetCount": set_count,
            "directExerciseSetId": direct_set_id if set_count == 1 else None,
        }
        for task, topic_count, set_count, direct_set_id in rows
    ]


@router.get("/catalog/tasks/{task_number}")
async def get_exam_task(task_number: int, db: AsyncSession = Depends(get_db)):
    task = await db.scalar(
        select(ExamTaskBD)
        .join(CourseVersionBD, CourseVersionBD.id == ExamTaskBD.course_version_id)
        .where(
            ExamTaskBD.number == task_number,
            ExamTaskBD.status == "published",
            CourseVersionBD.is_active.is_(True),
        )
    )
    if task is None:
        raise HTTPException(404, "Exam task not found")
    topics = (
        await db.scalars(
            select(TopicBD)
            .join(ExamTaskTopicBD, ExamTaskTopicBD.topic_id == TopicBD.id)
            .where(
                ExamTaskTopicBD.exam_task_id == task.id,
                TopicBD.status.in_(VISIBLE_TOPIC_STATUSES),
            )
            .order_by(ExamTaskTopicBD.sort_order, TopicBD.title)
        )
    ).all()
    return {
        **_task_out(task, len(topics)),
        "topics": [_topic_out(topic) for topic in topics],
        "theory": await _published_document(db, exam_task_id=task.id),
    }


@router.get("/theory/topics/{topic_id}")
async def get_topic_theory(topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.scalar(
        select(TopicBD).where(TopicBD.id == topic_id, TopicBD.status.in_(VISIBLE_TOPIC_STATUSES))
    )
    if topic is None:
        raise HTTPException(404, "Topic not found")
    task_numbers = (
        await db.scalars(
            select(ExamTaskBD.number)
            .join(ExamTaskTopicBD, ExamTaskTopicBD.exam_task_id == ExamTaskBD.id)
            .where(ExamTaskTopicBD.topic_id == topic.id)
            .order_by(ExamTaskBD.number)
        )
    ).all()
    return {
        **_topic_out(topic),
        "taskNumbers": list(task_numbers),
        "theory": await _published_document(db, topic_id=topic.id),
    }


@router.get("/theory/deprecated")
async def list_deprecated_theory(db: AsyncSession = Depends(get_db)):
    """Read-only catalog of theory imported from the legacy application."""
    versions = list((await db.scalars(
        select(TheoryDocumentVersionBD)
        .join(TheoryDocumentBD, TheoryDocumentBD.id == TheoryDocumentVersionBD.document_id)
        .where(TheoryDocumentVersionBD.source_legacy_theory_id.is_not(None))
        .order_by(TheoryDocumentVersionBD.source_legacy_theory_id)
    )).all())
    result = []
    for version in versions:
        document = await db.get(TheoryDocumentBD, version.document_id)
        task = None
        topic = None
        if document.exam_task_id is not None:
            task = await db.get(ExamTaskBD, document.exam_task_id)
        elif document.topic_id is not None:
            topic = await db.get(TopicBD, document.topic_id)
            task = await db.scalar(
                select(ExamTaskBD)
                .join(ExamTaskTopicBD, ExamTaskTopicBD.exam_task_id == ExamTaskBD.id)
                .where(ExamTaskTopicBD.topic_id == topic.id)
                .order_by(ExamTaskTopicBD.is_primary.desc(), ExamTaskBD.number)
                .limit(1)
            )
        result.append({
            "versionId": version.id,
            "legacyTheoryId": version.source_legacy_theory_id,
            "title": document.title,
            "taskNumber": task.number if task else None,
            "topicTitle": topic.title if topic else None,
        })
    return result


@router.get("/theory/deprecated/{version_id}")
async def get_deprecated_theory(version_id: int, db: AsyncSession = Depends(get_db)):
    version = await db.scalar(select(TheoryDocumentVersionBD).where(
        TheoryDocumentVersionBD.id == version_id,
        TheoryDocumentVersionBD.source_legacy_theory_id.is_not(None),
    ))
    if version is None:
        raise HTTPException(404, "Deprecated theory version not found")
    document = await db.get(TheoryDocumentBD, version.document_id)
    blocks = list((await db.scalars(
        select(TheoryBlockV2BD)
        .where(TheoryBlockV2BD.document_version_id == version.id)
        .order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id)
    )).all())
    return {
        "id": document.id,
        "title": document.title,
        "version": version.version_number,
        "legacyTheoryId": version.source_legacy_theory_id,
        "blocks": _block_tree(blocks),
    }


@router.get("/practice/tasks/{task_number}/sets")
async def list_exercise_sets(
    task_number: int,
    topic_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    task = await db.scalar(
        select(ExamTaskBD)
        .join(CourseVersionBD, CourseVersionBD.id == ExamTaskBD.course_version_id)
        .where(
            ExamTaskBD.number == task_number,
            ExamTaskBD.status == "published",
            CourseVersionBD.is_active.is_(True),
        )
    )
    if task is None:
        raise HTTPException(404, "Exam task not found")
    conditions = [
        ExerciseSetBD.exam_task_id == task.id,
        ExerciseSetBD.status == "published",
    ]
    if topic_id is not None:
        conditions.append(ExerciseSetBD.topic_id == topic_id)
    rows = (
        await db.execute(
            select(
                ExerciseSetBD,
                TopicBD.title,
                func.count(ExerciseSetItemBD.id).label("exercise_count"),
            )
            .outerjoin(TopicBD, TopicBD.id == ExerciseSetBD.topic_id)
            .outerjoin(
                ExerciseSetItemBD,
                ExerciseSetItemBD.exercise_set_id == ExerciseSetBD.id,
            )
            .where(*conditions)
            .group_by(ExerciseSetBD.id, TopicBD.title)
            .order_by(ExerciseSetBD.id)
        )
    ).all()
    return {
        "task": _task_out(task),
        "sets": [
            {
                "id": exercise_set.id,
                "title": exercise_set.title,
                "topicId": exercise_set.topic_id,
                "topicTitle": topic_title,
                "exerciseCount": exercise_count,
                "selectionStrategy": exercise_set.selection_strategy,
                "sessionSize": int(exercise_set.configuration.get("sessionSize", 50)),
                "pageSize": int(exercise_set.configuration.get("pageSize", 5)),
            }
            for exercise_set, topic_title, exercise_count in rows
        ],
    }


def _latest_attempt_ids(user_id: int):
    return (
        select(func.max(AttemptV2BD.id).label("attempt_id"))
        .join(
            ExerciseVersionBD,
            ExerciseVersionBD.id == AttemptV2BD.exercise_version_id,
        )
        .where(AttemptV2BD.user_id == user_id)
        .group_by(ExerciseVersionBD.exercise_id)
        .subquery()
    )


@router.get("/practice/mistakes")
async def list_practice_mistakes(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    latest = _latest_attempt_ids(user_id)
    rows = (
        await db.execute(
            select(
                ExamTaskBD.number,
                ExamTaskBD.title,
                func.count(func.distinct(ExerciseBD.id)),
            )
            .join(
                ExerciseTaskLinkBD,
                ExerciseTaskLinkBD.exam_task_id == ExamTaskBD.id,
            )
            .join(ExerciseBD, ExerciseBD.id == ExerciseTaskLinkBD.exercise_id)
            .join(
                ExerciseVersionBD,
                ExerciseVersionBD.exercise_id == ExerciseBD.id,
            )
            .join(
                AttemptV2BD,
                AttemptV2BD.exercise_version_id == ExerciseVersionBD.id,
            )
            .join(latest, latest.c.attempt_id == AttemptV2BD.id)
            .where(AttemptV2BD.result_status.in_(("incorrect", "partial")))
            .group_by(ExamTaskBD.id)
            .order_by(ExamTaskBD.number)
        )
    ).all()
    return {
        "total": sum(count for _, _, count in rows),
        "tasks": [
            {"number": number, "title": title, "count": count}
            for number, title, count in rows
        ],
    }


def _public_question(
    item: PracticeSessionItemBD,
    version: ExerciseVersionBD,
    attempt: AttemptV2BD | None = None,
) -> dict[str, Any]:
    result = None
    if attempt is not None:
        if version.checker_type == "exact_option":
            correct_response = {
                "optionKey": version.answer_config.get("correctOptionKey")
            }
        elif version.checker_type == "set_equality":
            correct_response = {
                "optionKeys": version.answer_config.get("correctOptionKeys", [])
            }
        elif version.checker_type == "exact_position":
            correct_response = {
                "selectedCharacterIndex": version.answer_config.get(
                    "correctCharacterIndex"
                )
            }
        else:
            accepted = version.answer_config.get("acceptedAnswers", [])
            correct_response = {"text": accepted[0] if accepted else None}
        result = {
            "attemptId": attempt.id,
            "status": attempt.result_status,
            "score": attempt.score,
            "response": attempt.response_data,
            "correctResponse": correct_response,
            "correctAnswer": version.feedback_data.get("correctAnswer"),
        }
    return {
        "sessionItemId": item.id,
        "position": item.position,
        "state": item.state,
        "interactionType": version.interaction_type,
        "responseSchemaVersion": version.response_schema_version,
        "prompt": version.prompt_data,
        "interaction": version.interaction_config,
        "result": result,
    }


async def _session_out(
    db: AsyncSession,
    session: PracticeSessionBD,
) -> dict[str, Any]:
    context = (
        await db.execute(
            select(
                ExerciseSetBD.title,
                ExamTaskBD.number,
                ExamTaskBD.title,
                TopicBD.id,
                TopicBD.title,
            )
            .join(ExamTaskBD, ExamTaskBD.id == ExerciseSetBD.exam_task_id)
            .outerjoin(TopicBD, TopicBD.id == ExerciseSetBD.topic_id)
            .where(ExerciseSetBD.id == session.exercise_set_id)
        )
    ).one()
    rows = (
        await db.execute(
            select(PracticeSessionItemBD, ExerciseVersionBD)
            .join(
                ExerciseVersionBD,
                ExerciseVersionBD.id == PracticeSessionItemBD.exercise_version_id,
            )
            .where(PracticeSessionItemBD.session_id == session.id)
            .order_by(PracticeSessionItemBD.position)
        )
    ).all()
    attempts = (
        await db.scalars(
            select(AttemptV2BD)
            .join(
                PracticeSessionItemBD,
                PracticeSessionItemBD.id == AttemptV2BD.session_item_id,
            )
            .where(PracticeSessionItemBD.session_id == session.id)
            .order_by(AttemptV2BD.id)
        )
    ).all()
    latest_attempts = {attempt.session_item_id: attempt for attempt in attempts}
    return {
        "id": session.id,
        "mode": session.mode,
        "status": session.status,
        "currentPosition": session.current_position,
        "exerciseSetId": session.exercise_set_id,
        "configuration": session.configuration,
        "context": {
            "setTitle": context[0],
            "taskNumber": context[1],
            "taskTitle": context[2],
            "topicId": context[3],
            "topicTitle": context[4],
        },
        "items": [
            _public_question(item, version, latest_attempts.get(item.id))
            for item, version in rows
        ],
    }


async def _letter_keys_for_set(
    db: AsyncSession,
    exercise_set_id: int,
) -> list[str]:
    versions = (
        await db.scalars(
            select(ExerciseVersionBD)
            .join(
                ExerciseBD,
                ExerciseBD.published_version_id == ExerciseVersionBD.id,
            )
            .join(
                ExerciseSetItemBD,
                ExerciseSetItemBD.exercise_id == ExerciseBD.id,
            )
            .where(
                ExerciseSetItemBD.exercise_set_id == exercise_set_id,
                ExerciseVersionBD.interaction_type == "vowel_fill",
            )
        )
    ).all()
    letters: set[str] = set()
    for version in versions:
        mask = str(version.interaction_config.get("mask") or "")
        accepted = version.answer_config.get("acceptedAnswers") or []
        if not accepted:
            continue
        answer = str(accepted[0])
        for position, character in enumerate(mask):
            if character in {"_", "…"} and position < len(answer):
                letters.add(answer[position].casefold())
    # Legacy ``vowel_fill`` is also used for consonants and hard/soft signs.
    # Keep the familiar vowels first, then expose every other Russian letter
    # actually required by this set instead of making those rows impossible.
    preferred_order = "аоеёиыуюяэбвгджзйклмнпрстфхцчшщъь"
    return [letter for letter in preferred_order if letter in letters]


@router.post("/practice/sessions", status_code=201)
async def create_practice_session(
    body: SessionCreateIn,
    db: AsyncSession = Depends(get_db),
):
    exercise_set = await db.scalar(
        select(ExerciseSetBD).where(
            ExerciseSetBD.id == body.exercise_set_id,
            ExerciseSetBD.status == "published",
        )
    )
    if exercise_set is None:
        raise HTTPException(404, "Exercise set not found")
    limit = body.limit or int(exercise_set.configuration.get("sessionSize", 50))
    page_size = body.page_size or int(exercise_set.configuration.get("pageSize", 5))
    page_size = min(page_size, limit)
    now = datetime.now(timezone.utc)
    owner_condition = (
        PracticeSessionBD.user_id == body.user_id
        if body.user_id is not None
        else PracticeSessionBD.configuration["clientSessionId"].astext
        == body.client_session_id
    )
    if body.user_id is not None or body.client_session_id:
        previous_sessions = list(
            (
                await db.scalars(
                    select(PracticeSessionBD)
                    .where(
                        PracticeSessionBD.exercise_set_id == exercise_set.id,
                        PracticeSessionBD.mode == body.mode,
                        PracticeSessionBD.status == "active",
                        owner_condition,
                    )
                    .order_by(PracticeSessionBD.last_activity_at.desc())
                )
            ).all()
        )
        for previous in previous_sessions:
            paused_at_raw = (previous.configuration or {}).get("pausedAt")
            reference_time = previous.last_activity_at
            if paused_at_raw:
                try:
                    reference_time = datetime.fromisoformat(paused_at_raw)
                except ValueError:
                    reference_time = previous.last_activity_at
            if now - reference_time <= timedelta(minutes=10):
                previous.configuration = {
                    **(previous.configuration or {}),
                    "pausedAt": None,
                }
                previous.last_activity_at = now
                await db.commit()
                return await _session_out(db, previous)
            previous.status = "expired"
            previous.completed_at = now
        if previous_sessions:
            await db.flush()
    query = (
        select(ExerciseBD.published_version_id)
        .join(ExerciseSetItemBD, ExerciseSetItemBD.exercise_id == ExerciseBD.id)
        .where(
            ExerciseSetItemBD.exercise_set_id == exercise_set.id,
            ExerciseBD.status == "published",
            ExerciseBD.published_version_id.is_not(None),
        )
    )
    if body.mode == "mistakes":
        if body.user_id is None:
            raise HTTPException(400, "Mistake practice requires a user")
        latest = _latest_attempt_ids(body.user_id)
        mistake_exercises = (
            select(ExerciseVersionBD.exercise_id)
            .join(
                AttemptV2BD,
                AttemptV2BD.exercise_version_id == ExerciseVersionBD.id,
            )
            .join(latest, latest.c.attempt_id == AttemptV2BD.id)
            .where(AttemptV2BD.result_status.in_(("incorrect", "partial")))
        )
        query = query.where(ExerciseBD.id.in_(mistake_exercises))
    if body.user_id is not None or body.client_session_id:
        seen_query = (
            select(
                ExerciseVersionBD.exercise_id.label("exercise_id"),
                func.count(AttemptV2BD.id).label("seen_count"),
                func.max(AttemptV2BD.submitted_at).label("last_seen_at"),
            )
            .join(
                AttemptV2BD,
                AttemptV2BD.exercise_version_id == ExerciseVersionBD.id,
            )
        )
        if body.user_id is not None:
            seen_query = seen_query.where(AttemptV2BD.user_id == body.user_id)
        else:
            seen_query = (
                seen_query
                .join(
                    PracticeSessionItemBD,
                    PracticeSessionItemBD.id == AttemptV2BD.session_item_id,
                )
                .join(
                    PracticeSessionBD,
                    PracticeSessionBD.id == PracticeSessionItemBD.session_id,
                )
                .where(
                    PracticeSessionBD.configuration["clientSessionId"].astext
                    == body.client_session_id
                )
            )
        seen = (
            seen_query
            .group_by(ExerciseVersionBD.exercise_id)
            .subquery()
        )
        query = (
            query.outerjoin(seen, seen.c.exercise_id == ExerciseBD.id)
            .order_by(
                func.coalesce(seen.c.seen_count, 0),
                seen.c.last_seen_at.asc().nullsfirst(),
                func.random(),
            )
        )
    else:
        query = query.order_by(func.random())
    version_ids = list((await db.scalars(query.limit(limit))).all())
    if not version_ids:
        raise HTTPException(409, "Exercise set is empty")
    session_configuration = {
        "sessionSize": limit,
        "pageSize": page_size,
        "promptDisplay": exercise_set.configuration.get("promptDisplay", "normal"),
        "showSingleLetterSuccess": bool(
            exercise_set.configuration.get("showSingleLetterSuccess", False)
        ),
        "clientSessionId": body.client_session_id,
        "pausedAt": None,
    }
    letter_keys = await _letter_keys_for_set(db, exercise_set.id)
    if letter_keys:
        session_configuration["letterKeys"] = letter_keys
        # Kept during the API transition for already deployed frontend builds.
        session_configuration["vowelKeys"] = letter_keys
    session = PracticeSessionBD(
        user_id=body.user_id,
        exercise_set_id=exercise_set.id,
        mode=body.mode,
        status="active",
        current_position=0,
        configuration=session_configuration,
        last_activity_at=now,
    )
    db.add(session)
    await db.flush()
    for position, version_id in enumerate(version_ids):
        db.add(
            PracticeSessionItemBD(
                session_id=session.id,
                exercise_version_id=version_id,
                position=position,
                state="pending",
            )
        )
    await db.commit()
    return await _session_out(db, session)


@router.get("/practice/sessions/{session_id}")
async def get_practice_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(PracticeSessionBD, session_id)
    if session is None:
        raise HTTPException(404, "Practice session not found")
    paused_at_raw = (session.configuration or {}).get("pausedAt")
    if session.status == "active" and paused_at_raw:
        now = datetime.now(timezone.utc)
        try:
            paused_at = datetime.fromisoformat(paused_at_raw)
        except ValueError:
            paused_at = session.last_activity_at
        if now - paused_at > timedelta(minutes=10):
            session.status = "expired"
            session.completed_at = now
        else:
            session.configuration = {
                **(session.configuration or {}),
                "pausedAt": None,
            }
            session.last_activity_at = now
        await db.commit()
    return await _session_out(db, session)


def _check_answer(
    version: ExerciseVersionBD,
    response: dict[str, Any],
) -> tuple[Literal["incorrect", "partial", "correct"], float, dict[str, Any]]:
    if version.checker_type == "exact_option":
        raw = response.get("optionKey")
        correct = version.answer_config.get("correctOptionKey")
        is_correct = raw == correct
        normalized = {"optionKey": raw}
    elif version.checker_type == "set_equality":
        raw = response.get("optionKeys")
        selected = {
            str(value) for value in raw
        } if isinstance(raw, list) else set()
        correct_set = {
            str(value) for value in version.answer_config.get("correctOptionKeys", [])
        }
        overlap = len(selected & correct_set)
        is_correct = bool(correct_set) and selected == correct_set
        score = overlap / len(selected | correct_set) if correct_set else 0.0
        normalized = {"optionKeys": sorted(selected)}
        if is_correct:
            return "correct", 1.0, normalized
        if overlap:
            return "partial", score, normalized
        return "incorrect", 0.0, normalized
    elif version.checker_type == "exact_position":
        raw = response.get("selectedCharacterIndex")
        correct = version.answer_config.get("correctCharacterIndex")
        is_correct = isinstance(raw, int) and raw == correct
        normalized = {"selectedCharacterIndex": raw}
    elif version.checker_type == "normalized_text":
        raw = str(response.get("text") or "")
        config = version.checker_config
        normalized_text = raw.strip() if config.get("trim", True) else raw
        accepted = [
            str(value).strip() if config.get("trim", True) else str(value)
            for value in version.answer_config.get("acceptedAnswers", [])
        ]
        if config.get("caseInsensitive", True):
            normalized_text = normalized_text.casefold()
            accepted = [value.casefold() for value in accepted]
        is_correct = normalized_text in accepted
        normalized = {"text": normalized_text}
    else:
        raise HTTPException(409, "Exercise checker is not supported")
    return ("correct" if is_correct else "incorrect"), (1.0 if is_correct else 0.0), normalized


async def _theory_links(
    db: AsyncSession,
    exercise_version: ExerciseVersionBD,
) -> list[dict[str, Any]]:
    exercise_id = exercise_version.exercise_id
    topic_rows = (
        await db.execute(
            select(TopicBD.id, TopicBD.title, ExamTaskBD.number)
            .join(ExerciseTopicLinkBD, ExerciseTopicLinkBD.topic_id == TopicBD.id)
            .join(
                ExamTaskTopicBD,
                ExamTaskTopicBD.topic_id == TopicBD.id,
            )
            .join(ExamTaskBD, ExamTaskBD.id == ExamTaskTopicBD.exam_task_id)
            .where(ExerciseTopicLinkBD.exercise_id == exercise_id)
            .order_by(ExerciseTopicLinkBD.is_primary.desc(), ExamTaskBD.number)
        )
    ).all()
    if topic_rows:
        return [
            {
                "label": title,
                "taskNumber": number,
                "topicId": topic_id,
                "route": f"/theory/tasks/{number}/topics/{topic_id}",
            }
            for topic_id, title, number in topic_rows
        ]
    task_rows = (
        await db.scalars(
            select(ExamTaskBD.number)
            .join(
                ExerciseTaskLinkBD,
                ExerciseTaskLinkBD.exam_task_id == ExamTaskBD.id,
            )
            .where(ExerciseTaskLinkBD.exercise_id == exercise_id)
            .order_by(ExerciseTaskLinkBD.is_primary.desc(), ExamTaskBD.number)
        )
    ).all()
    return [
        {
            "label": f"Теория задания {number}",
            "taskNumber": number,
            "topicId": None,
            "route": f"/theory/tasks/{number}",
        }
        for number in task_rows
    ]


@router.post("/practice/sessions/{session_id}/items/{item_id}/attempts")
async def submit_attempt(
    session_id: int,
    item_id: int,
    body: AnswerIn,
    db: AsyncSession = Depends(get_db),
):
    row = (
        await db.execute(
            select(PracticeSessionBD, PracticeSessionItemBD, ExerciseVersionBD)
            .join(
                PracticeSessionItemBD,
                PracticeSessionItemBD.session_id == PracticeSessionBD.id,
            )
            .join(
                ExerciseVersionBD,
                ExerciseVersionBD.id == PracticeSessionItemBD.exercise_version_id,
            )
            .where(
                PracticeSessionBD.id == session_id,
                PracticeSessionItemBD.id == item_id,
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Practice item not found")
    session, item, version = row
    if session.status != "active":
        raise HTTPException(409, "Practice session is not active")

    status, score, normalized = _check_answer(version, body.response)
    now = datetime.now(timezone.utc)
    checker_result = {"status": status, "score": score}
    attempt = AttemptV2BD(
        user_id=session.user_id,
        session_item_id=item.id,
        exercise_version_id=version.id,
        response_data=body.response,
        normalized_response=normalized,
        result_status=status,
        score=score,
        checker_result=checker_result,
        submitted_at=now,
    )
    db.add(attempt)
    item.state = status
    session.current_position = max(session.current_position, item.position + 1)
    session.last_activity_at = now
    session.configuration = {
        **(session.configuration or {}),
        "pausedAt": None,
    }
    pending_count = await db.scalar(
        select(func.count(PracticeSessionItemBD.id)).where(
            PracticeSessionItemBD.session_id == session.id,
            PracticeSessionItemBD.id != item.id,
            PracticeSessionItemBD.state == "pending",
        )
    )
    if pending_count == 0:
        session.status = "completed"
        session.completed_at = now
    await db.commit()
    return {
        "attemptId": attempt.id,
        "status": status,
        "score": score,
        "correctAnswer": version.feedback_data.get("correctAnswer"),
        "response": body.response,
        "correctResponse": (
            {"optionKey": version.answer_config.get("correctOptionKey")}
            if version.checker_type == "exact_option"
            else {"optionKeys": version.answer_config.get("correctOptionKeys", [])}
            if version.checker_type == "set_equality"
            else {
                "selectedCharacterIndex": version.answer_config.get(
                    "correctCharacterIndex"
                )
            }
            if version.checker_type == "exact_position"
            else {
                "text": (version.answer_config.get("acceptedAnswers") or [None])[0]
            }
        ),
        "feedback": {
            "message": version.feedback_data.get(
                "correct" if status == "correct" else "incorrect"
            ),
            "theoryLinks": await _theory_links(db, version),
        },
        "sessionStatus": session.status,
    }


@router.post("/practice/sessions/{session_id}/close")
async def close_practice_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(PracticeSessionBD, session_id)
    if session is None:
        raise HTTPException(404, "Practice session not found")
    if session.status == "active":
        now = datetime.now(timezone.utc)
        session.status = "closed"
        session.completed_at = now
        session.last_activity_at = now
        await db.commit()
    return {"id": session.id, "status": session.status}


@router.post("/practice/sessions/{session_id}/pause")
async def pause_practice_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(PracticeSessionBD, session_id)
    if session is None:
        raise HTTPException(404, "Practice session not found")
    if session.status == "active":
        now = datetime.now(timezone.utc)
        session.configuration = {
            **(session.configuration or {}),
            "pausedAt": now.isoformat(),
        }
        session.last_activity_at = now
        await db.commit()
    return {"id": session.id, "status": session.status}


@router.post("/practice/sessions/{session_id}/reset")
async def reset_practice_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(PracticeSessionBD, session_id)
    if session is None:
        raise HTTPException(404, "Practice session not found")
    if session.status == "active":
        now = datetime.now(timezone.utc)
        session.status = "reset"
        session.completed_at = now
        session.last_activity_at = now
        session.configuration = {
            **(session.configuration or {}),
            "pausedAt": None,
        }
        await db.commit()
    return {"id": session.id, "status": session.status}
