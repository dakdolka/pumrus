from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import or_, select
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
VISIBLE_TOPIC_STATUSES = ("published", "published_manual")


def _temporal(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _timestamps(item: Any) -> dict[str, str | None]:
    return {
        "createdAt": _temporal(item.created_at),
        "updatedAt": _temporal(item.updated_at),
    }


async def _catalog(
    db: AsyncSession,
    include_history: bool,
) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    version_query = select(CourseVersionBD)
    if not include_history:
        version_query = version_query.where(CourseVersionBD.is_active.is_(True))
    course_versions = list((await db.scalars(
        version_query.order_by(CourseVersionBD.course_id, CourseVersionBD.id)
    )).all())
    course_ids = {item.course_id for item in course_versions}
    courses = list((await db.scalars(
        select(CourseBD).where(CourseBD.id.in_(course_ids)).order_by(CourseBD.id)
    )).all()) if course_ids else []
    version_ids = {item.id for item in course_versions}
    tasks = list((await db.scalars(
        select(ExamTaskBD)
        .where(ExamTaskBD.course_version_id.in_(version_ids))
        .order_by(
            ExamTaskBD.course_version_id,
            ExamTaskBD.sort_order,
            ExamTaskBD.number,
            ExamTaskBD.id,
        )
    )).all()) if version_ids else []
    topic_query = select(TopicBD).where(TopicBD.course_version_id.in_(version_ids))
    if not include_history:
        topic_query = topic_query.where(TopicBD.status.in_(VISIBLE_TOPIC_STATUSES))
    topics = list((await db.scalars(
        topic_query.order_by(TopicBD.course_version_id, TopicBD.id)
    )).all()) if version_ids else []
    task_ids = {item.id for item in tasks}
    topic_ids = {item.id for item in topics}
    task_topic_links = list((await db.scalars(
        select(ExamTaskTopicBD)
        .where(
            ExamTaskTopicBD.exam_task_id.in_(task_ids),
            ExamTaskTopicBD.topic_id.in_(topic_ids),
        )
        .order_by(
            ExamTaskTopicBD.exam_task_id,
            ExamTaskTopicBD.sort_order,
            ExamTaskTopicBD.topic_id,
        )
    )).all()) if task_ids and topic_ids else []

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


def _envelope(
    kind: str,
    catalog: dict[str, Any],
    include_history: bool,
) -> dict[str, Any]:
    return {
        "schemaVersion": EXPORT_SCHEMA_VERSION,
        "kind": kind,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "all-course-versions" if include_history else "active-course-version",
        "includeHistory": include_history,
        "catalog": catalog,
    }


async def build_theory_export(
    db: AsyncSession,
    include_history: bool = False,
) -> dict[str, Any]:
    catalog, refs = await _catalog(db, include_history)
    document_query = select(TheoryDocumentBD)
    if not include_history:
        task_ids = {item.id for item in refs["tasks"]}
        topic_ids = {item.id for item in refs["topics"]}
        document_query = document_query.where(
            TheoryDocumentBD.status == "published",
            TheoryDocumentBD.published_version_id.is_not(None),
            or_(
                TheoryDocumentBD.exam_task_id.in_(task_ids),
                TheoryDocumentBD.topic_id.in_(topic_ids),
            ),
        )
    documents = list((await db.scalars(
        document_query.order_by(TheoryDocumentBD.id)
    )).all())
    version_query = select(TheoryDocumentVersionBD)
    if not include_history:
        published_version_ids = {
            item.published_version_id for item in documents
            if item.published_version_id is not None
        }
        version_query = version_query.where(
            TheoryDocumentVersionBD.id.in_(published_version_ids)
        )
    versions = list((await db.scalars(
        version_query.order_by(
            TheoryDocumentVersionBD.document_id,
            TheoryDocumentVersionBD.version_number,
            TheoryDocumentVersionBD.id,
        )
    )).all())
    version_ids = {item.id for item in versions}
    blocks = list((await db.scalars(
        select(TheoryBlockV2BD)
        .where(TheoryBlockV2BD.document_version_id.in_(version_ids))
        .order_by(
            TheoryBlockV2BD.document_version_id,
            TheoryBlockV2BD.sort_order,
            TheoryBlockV2BD.id,
        )
    )).all()) if version_ids else []

    payload = _envelope("theory", catalog, include_history)
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


async def build_practice_export(
    db: AsyncSession,
    include_history: bool = False,
) -> dict[str, Any]:
    catalog, refs = await _catalog(db, include_history)
    task_ids = {item.id for item in refs["tasks"]}
    topic_ids = {item.id for item in refs["topics"]}
    version_ids = {item.id for item in refs["courseVersions"]}

    task_document_query = select(TaskDocumentBD)
    exercise_set_query = select(ExerciseSetBD)
    if not include_history:
        task_document_query = task_document_query.where(
            TaskDocumentBD.exam_task_id.in_(task_ids),
            TaskDocumentBD.status == "published",
        )
        exercise_set_query = exercise_set_query.where(
            ExerciseSetBD.course_version_id.in_(version_ids),
            ExerciseSetBD.exam_task_id.in_(task_ids),
            ExerciseSetBD.status == "published",
            or_(
                ExerciseSetBD.topic_id.is_(None),
                ExerciseSetBD.topic_id.in_(topic_ids),
            ),
        )
    task_documents = list((await db.scalars(
        task_document_query.order_by(TaskDocumentBD.exam_task_id, TaskDocumentBD.id)
    )).all())
    exercise_sets = list((await db.scalars(
        exercise_set_query.order_by(
            ExerciseSetBD.course_version_id,
            ExerciseSetBD.exam_task_id,
            ExerciseSetBD.id,
        )
    )).all())
    exercise_set_ids = {item.id for item in exercise_sets}
    set_item_query = select(ExerciseSetItemBD)
    if not include_history:
        set_item_query = set_item_query.where(
            ExerciseSetItemBD.exercise_set_id.in_(exercise_set_ids)
        )
    set_items = list((await db.scalars(
        set_item_query.order_by(
            ExerciseSetItemBD.exercise_set_id,
            ExerciseSetItemBD.sort_order,
            ExerciseSetItemBD.id,
        )
    )).all())
    included_exercise_ids = {item.exercise_id for item in set_items}
    exercise_query = select(ExerciseBD)
    if not include_history:
        exercise_query = exercise_query.where(
            ExerciseBD.id.in_(included_exercise_ids),
            ExerciseBD.status == "published",
            ExerciseBD.published_version_id.is_not(None),
        )
    exercises = list((await db.scalars(
        exercise_query.order_by(ExerciseBD.course_version_id, ExerciseBD.id)
    )).all())
    exercise_ids = {item.id for item in exercises}
    if not include_history:
        set_items = [item for item in set_items if item.exercise_id in exercise_ids]
    exercise_version_query = select(ExerciseVersionBD)
    if not include_history:
        published_version_ids = {
            item.published_version_id for item in exercises
            if item.published_version_id is not None
        }
        exercise_version_query = exercise_version_query.where(
            ExerciseVersionBD.id.in_(published_version_ids)
        )
    versions = list((await db.scalars(
        exercise_version_query.order_by(
            ExerciseVersionBD.exercise_id,
            ExerciseVersionBD.version_number,
            ExerciseVersionBD.id,
        )
    )).all())
    task_link_query = select(ExerciseTaskLinkBD)
    topic_link_query = select(ExerciseTopicLinkBD)
    if not include_history:
        task_link_query = task_link_query.where(
            ExerciseTaskLinkBD.exercise_id.in_(exercise_ids),
            ExerciseTaskLinkBD.exam_task_id.in_(task_ids),
        )
        topic_link_query = topic_link_query.where(
            ExerciseTopicLinkBD.exercise_id.in_(exercise_ids),
            ExerciseTopicLinkBD.topic_id.in_(topic_ids),
        )
    task_links = list((await db.scalars(
        task_link_query.order_by(
            ExerciseTaskLinkBD.exercise_id,
            ExerciseTaskLinkBD.exam_task_id,
        )
    )).all())
    topic_links = list((await db.scalars(
        topic_link_query.order_by(
            ExerciseTopicLinkBD.exercise_id,
            ExerciseTopicLinkBD.topic_id,
        )
    )).all())

    payload = _envelope("practice", catalog, include_history)
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
                "accessLevel": item.access_level,
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
                "isPreview": item.is_preview,
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
