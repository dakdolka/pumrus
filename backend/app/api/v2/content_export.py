from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.catalog.models import (
    CourseBD,
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
    TaskDocumentBD,
)


EXPORT_SCHEMA_VERSION = 1


def _temporal(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _timestamps(item: Any) -> dict[str, str | None]:
    return {
        "createdAt": _temporal(item.created_at),
        "updatedAt": _temporal(item.updated_at),
    }


async def _catalog(db: AsyncSession) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    courses = list((await db.scalars(select(CourseBD).order_by(CourseBD.id))).all())
    course_versions = list((await db.scalars(
        select(CourseVersionBD).order_by(CourseVersionBD.course_id, CourseVersionBD.id)
    )).all())
    tasks = list((await db.scalars(
        select(ExamTaskBD).order_by(
            ExamTaskBD.course_version_id,
            ExamTaskBD.sort_order,
            ExamTaskBD.number,
            ExamTaskBD.id,
        )
    )).all())
    topics = list((await db.scalars(
        select(TopicBD).order_by(TopicBD.course_version_id, TopicBD.id)
    )).all())
    task_topic_links = list((await db.scalars(
        select(ExamTaskTopicBD).order_by(
            ExamTaskTopicBD.exam_task_id,
            ExamTaskTopicBD.sort_order,
            ExamTaskTopicBD.topic_id,
        )
    )).all())

    payload = {
        "courses": [
            {
                "id": item.id,
                "code": item.code,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                **_timestamps(item),
            }
            for item in courses
        ],
        "courseVersions": [
            {
                "id": item.id,
                "courseId": item.course_id,
                "code": item.code,
                "title": item.title,
                "validFrom": _temporal(item.valid_from),
                "validTo": _temporal(item.valid_to),
                "status": item.status,
                "isActive": item.is_active,
                **_timestamps(item),
            }
            for item in course_versions
        ],
        "tasks": [
            {
                "id": item.id,
                "courseVersionId": item.course_version_id,
                "code": item.code,
                "number": item.number,
                "title": item.title,
                "shortDescription": item.short_description,
                "sortOrder": item.sort_order,
                "status": item.status,
                **_timestamps(item),
            }
            for item in tasks
        ],
        "topics": [
            {
                "id": item.id,
                "courseVersionId": item.course_version_id,
                "code": item.code,
                "title": item.title,
                "shortDescription": item.short_description,
                "status": item.status,
                "sourceLegacyTheoryId": item.source_legacy_theory_id,
                **_timestamps(item),
            }
            for item in topics
        ],
        "taskTopicLinks": [
            {
                "taskId": item.exam_task_id,
                "topicId": item.topic_id,
                "sortOrder": item.sort_order,
                "isPrimary": item.is_primary,
                **_timestamps(item),
            }
            for item in task_topic_links
        ],
    }
    return payload, {
        "courses": courses,
        "courseVersions": course_versions,
        "tasks": tasks,
        "topics": topics,
        "taskTopicLinks": task_topic_links,
    }


def _envelope(kind: str, catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": EXPORT_SCHEMA_VERSION,
        "kind": kind,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "all-course-versions",
        "catalog": catalog,
    }


async def build_theory_export(db: AsyncSession) -> dict[str, Any]:
    catalog, _ = await _catalog(db)
    documents = list((await db.scalars(
        select(TheoryDocumentBD).order_by(TheoryDocumentBD.id)
    )).all())
    versions = list((await db.scalars(
        select(TheoryDocumentVersionBD).order_by(
            TheoryDocumentVersionBD.document_id,
            TheoryDocumentVersionBD.version_number,
            TheoryDocumentVersionBD.id,
        )
    )).all())
    blocks = list((await db.scalars(
        select(TheoryBlockV2BD).order_by(
            TheoryBlockV2BD.document_version_id,
            TheoryBlockV2BD.sort_order,
            TheoryBlockV2BD.id,
        )
    )).all())

    payload = _envelope("theory", catalog)
    payload["theory"] = {
        "documents": [
            {
                "id": item.id,
                "taskId": item.exam_task_id,
                "topicId": item.topic_id,
                "title": item.title,
                "status": item.status,
                "publishedVersionId": item.published_version_id,
                **_timestamps(item),
            }
            for item in documents
        ],
        "documentVersions": [
            {
                "id": item.id,
                "documentId": item.document_id,
                "versionNumber": item.version_number,
                "status": item.status,
                "sourceLegacyTheoryId": item.source_legacy_theory_id,
                "publishedAt": _temporal(item.published_at),
                **_timestamps(item),
            }
            for item in versions
        ],
        "blocks": [
            {
                "id": item.id,
                "documentVersionId": item.document_version_id,
                "parentBlockId": item.parent_block_id,
                "type": item.block_type,
                "schemaVersion": item.schema_version,
                "data": item.data,
                "settings": item.settings,
                "sortOrder": item.sort_order,
                "sourceLegacyBlockId": item.source_legacy_block_id,
                **_timestamps(item),
            }
            for item in blocks
        ],
    }
    payload["counts"] = {
        "documents": len(documents),
        "documentVersions": len(versions),
        "blocks": len(blocks),
    }
    return payload


async def build_practice_export(db: AsyncSession) -> dict[str, Any]:
    catalog, _ = await _catalog(db)
    task_documents = list((await db.scalars(
        select(TaskDocumentBD).order_by(TaskDocumentBD.exam_task_id, TaskDocumentBD.id)
    )).all())
    exercises = list((await db.scalars(
        select(ExerciseBD).order_by(ExerciseBD.course_version_id, ExerciseBD.id)
    )).all())
    versions = list((await db.scalars(
        select(ExerciseVersionBD).order_by(
            ExerciseVersionBD.exercise_id,
            ExerciseVersionBD.version_number,
            ExerciseVersionBD.id,
        )
    )).all())
    task_links = list((await db.scalars(
        select(ExerciseTaskLinkBD).order_by(
            ExerciseTaskLinkBD.exercise_id,
            ExerciseTaskLinkBD.exam_task_id,
        )
    )).all())
    topic_links = list((await db.scalars(
        select(ExerciseTopicLinkBD).order_by(
            ExerciseTopicLinkBD.exercise_id,
            ExerciseTopicLinkBD.topic_id,
        )
    )).all())
    exercise_sets = list((await db.scalars(
        select(ExerciseSetBD).order_by(
            ExerciseSetBD.course_version_id,
            ExerciseSetBD.exam_task_id,
            ExerciseSetBD.id,
        )
    )).all())
    set_items = list((await db.scalars(
        select(ExerciseSetItemBD).order_by(
            ExerciseSetItemBD.exercise_set_id,
            ExerciseSetItemBD.sort_order,
            ExerciseSetItemBD.id,
        )
    )).all())

    payload = _envelope("practice", catalog)
    payload["practice"] = {
        "taskDocuments": [
            {
                "id": item.id,
                "taskId": item.exam_task_id,
                "title": item.title,
                "introduction": item.introduction,
                "configuration": item.configuration,
                "status": item.status,
                **_timestamps(item),
            }
            for item in task_documents
        ],
        "exercises": [
            {
                "id": item.id,
                "courseVersionId": item.course_version_id,
                "status": item.status,
                "difficulty": item.difficulty,
                "source": item.source,
                "sourceLegacyTaskItemId": item.source_legacy_task_item_id,
                "publishedVersionId": item.published_version_id,
                **_timestamps(item),
            }
            for item in exercises
        ],
        "exerciseVersions": [
            {
                "id": item.id,
                "exerciseId": item.exercise_id,
                "versionNumber": item.version_number,
                "status": item.status,
                "interactionType": item.interaction_type,
                "responseSchemaVersion": item.response_schema_version,
                "promptData": item.prompt_data,
                "interactionConfig": item.interaction_config,
                "answerConfig": item.answer_config,
                "checkerType": item.checker_type,
                "checkerConfig": item.checker_config,
                "feedbackData": item.feedback_data,
                "sourceLegacyTaskItemId": item.source_legacy_task_item_id,
                "publishedAt": _temporal(item.published_at),
                **_timestamps(item),
            }
            for item in versions
        ],
        "exerciseTaskLinks": [
            {
                "exerciseId": item.exercise_id,
                "taskId": item.exam_task_id,
                "isPrimary": item.is_primary,
                **_timestamps(item),
            }
            for item in task_links
        ],
        "exerciseTopicLinks": [
            {
                "exerciseId": item.exercise_id,
                "topicId": item.topic_id,
                "isPrimary": item.is_primary,
                **_timestamps(item),
            }
            for item in topic_links
        ],
        "exerciseSets": [
            {
                "id": item.id,
                "courseVersionId": item.course_version_id,
                "taskId": item.exam_task_id,
                "topicId": item.topic_id,
                "title": item.title,
                "selectionStrategy": item.selection_strategy,
                "configuration": item.configuration,
                "status": item.status,
                "sourceLegacyTaskId": item.source_legacy_task_id,
                **_timestamps(item),
            }
            for item in exercise_sets
        ],
        "exerciseSetItems": [
            {
                "id": item.id,
                "exerciseSetId": item.exercise_set_id,
                "exerciseId": item.exercise_id,
                "sortOrder": item.sort_order,
                "weight": item.weight,
                **_timestamps(item),
            }
            for item in set_items
        ],
    }
    payload["counts"] = {
        "taskDocuments": len(task_documents),
        "exercises": len(exercises),
        "exerciseVersions": len(versions),
        "exerciseSets": len(exercise_sets),
        "exerciseSetItems": len(set_items),
    }
    return payload
