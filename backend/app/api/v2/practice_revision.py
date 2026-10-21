"""Atomic publication of a reviewed practice bank, preserving exercise history."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, func, select

from app.api.v2.content_export import build_practice_export
from app.infra.catalog.models import ExamTaskBD
from app.infra.exercises.models import ExerciseBD, ExerciseVersionBD, ExerciseSetBD, ExerciseSetItemBD, ExerciseTaskLinkBD, ExerciseTopicLinkBD
from app.scripts.practice_scope_sync import _scope_config, _sync_membership, sync_preview_membership
from app.scripts.task10_11_revision import digest, legacy_lexeme, snapshot, stable, summary, validate_package, word_key


def payload(card, revision):
    return {
        "interaction_type": "vowel_fill",
        "prompt_data": {"content": card["prompt"], "format": "plain_text"},
        "interaction_config": {"variant": "masked_letters", "mask": card["prompt"]},
        "answer_config": {"acceptedAnswers": [card["answer"]]},
        "checker_type": "normalized_text",
        "checker_config": {"trim": True, "caseInsensitive": True, "yoPolicy": "distinct",
                           "curatedKey": card["curated_key"], "curatedRevision": revision,
                           "lexeme": card["lexeme"], "topicCode": card["topic_code"], "ruleId": card["rule_id"],
                           "isException": card["is_exception"], "sourceReferences": card["source_references"],
                           "dictionaryEvidence": card["dictionary_evidence"]},
        "feedback_data": {"correctAnswer": card["answer"], "correct": card["explanation"], "incorrect": card["explanation"]},
    }


def require_current(package, current):
    try:
        validate_package(package)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    if digest(current) != package["base"]["fingerprint"]:
        raise HTTPException(409, "Практика изменилась после экспорта. Подготовьте пакет на основе новой выгрузки")


async def preview(db, package):
    current = snapshot(await build_practice_export(db))
    require_current(package, current)
    return {"fingerprint": package["base"]["fingerprint"], "summary": summary(package)}


async def apply(db, package):
    try:
        validate_package(package)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    before = package["before"]
    task_ids = {item["id"] for item in before["tasks"]}
    topic_ids = {item["id"] for item in before["topics"]}
    old_ids = {item["id"] for item in before["exercises"]}
    set_ids = {item["id"] for item in before["sets"]}
    # Lock parents first, then existing records, before checking the export base.
    list((await db.scalars(select(ExamTaskBD).where(ExamTaskBD.id.in_(task_ids)).order_by(ExamTaskBD.id).with_for_update())).all())
    sets = list((await db.scalars(select(ExerciseSetBD).where(ExerciseSetBD.id.in_(set_ids)).order_by(ExerciseSetBD.id).with_for_update())).all())
    old_exercises = list((await db.scalars(select(ExerciseBD).where(ExerciseBD.id.in_(old_ids)).order_by(ExerciseBD.id).with_for_update())).all())
    current = snapshot(await build_practice_export(db))
    require_current(package, current)
    course_ids = {item["courseVersionId"] for item in before["tasks"]}
    if len(course_ids) != 1:
        raise HTTPException(422, "Выберите задания одной версии курса")
    course_id = next(iter(course_ids))
    if await db.scalar(select(ExerciseVersionBD.id).where(ExerciseVersionBD.exercise_id.in_(old_ids), ExerciseVersionBD.status == "draft").limit(1)):
        raise HTTPException(409, "У одного из упражнений есть черновик. Завершите его перед обновлением банка")

    exercises_by_id = {item.id: item for item in old_exercises}
    versions = {item["id"]: item for item in before["versions"]}
    task_links = defaultdict(set)
    for link in before["taskLinks"]:
        task_links[link["exerciseId"]].add(link["taskId"])
    # Protect any exercises also used by unrelated task sets.
    outside_ids = set((await db.scalars(select(ExerciseSetItemBD.exercise_id).where(ExerciseSetItemBD.exercise_id.in_(old_ids), ExerciseSetItemBD.exercise_set_id.not_in(set_ids)))).all())
    candidates = defaultdict(list)
    by_key = {}
    for item in before["exercises"]:
        if item["id"] in outside_ids or task_links[item["id"]] - task_ids:
            continue
        version = versions[item["publishedVersionId"]]
        candidates[legacy_lexeme(version)].append(item["id"])
        key = version.get("checkerConfig", {}).get("curatedKey")
        if key:
            by_key[key] = item["id"]
    max_versions = dict((await db.execute(select(ExerciseVersionBD.exercise_id, func.max(ExerciseVersionBD.version_number)).where(ExerciseVersionBD.exercise_id.in_(old_ids)).group_by(ExerciseVersionBD.exercise_id))).all())
    task_by_number = {item["number"]: item["id"] for item in before["tasks"]}
    plans, new_exercises, used = [], [], set()
    for topic in package["after"]["topics"]:
        for card in topic["cards"]:
            candidate = by_key.get(card["curated_key"])
            if candidate is None or candidate in used:
                candidate = next((item for item in candidates[word_key(card["lexeme"])] if item not in used), None)
            if candidate is None:
                exercise = ExerciseBD(course_version_id=course_id, status="published", source="reviewed_task10_11")
                new_exercises.append(exercise)
            else:
                exercise = exercises_by_id[candidate]
                used.add(candidate)
            plans.append((topic, card, exercise, payload(card, package["revision"])))
    db.add_all(new_exercises)
    await db.flush()
    counters = {"created": len(new_exercises), "updated": 0, "unchanged": 0, "retired": 0, "setsCreated": 0}
    now = datetime.now(timezone.utc)
    new_versions, old_version_ids = [], []
    for topic, card, exercise, values in plans:
        old = versions.get(exercise.published_version_id)
        old_values = {key: old.get({"interaction_type": "interactionType", "prompt_data": "promptData", "interaction_config": "interactionConfig", "answer_config": "answerConfig", "checker_type": "checkerType", "checker_config": "checkerConfig", "feedback_data": "feedbackData"}[key]) for key in values} if old else None
        if old_values is not None and stable(old_values) == stable(values):
            counters["unchanged"] += 1
            continue
        if old:
            old_version_ids.append(old["id"])
            counters["updated"] += 1
        version = ExerciseVersionBD(exercise_id=exercise.id, version_number=max_versions.get(exercise.id, 0) + 1,
                                    status="published", response_schema_version=1, published_at=now, **values)
        new_versions.append((exercise, version))
    if old_version_ids:
        for version in (await db.scalars(select(ExerciseVersionBD).where(ExerciseVersionBD.id.in_(old_version_ids)))).all():
            version.status = "archived"
    db.add_all([version for _, version in new_versions])
    await db.flush()
    for exercise, version in new_versions:
        exercise.published_version_id = version.id
        exercise.status = "published"
    used_ids = {exercise.id for _, _, exercise, _ in plans}
    retired = old_ids - used_ids - outside_ids
    for exercise_id in retired:
        if not (task_links[exercise_id] - task_ids):
            exercises_by_id[exercise_id].status = "archived"
            counters["retired"] += 1
    await db.execute(delete(ExerciseTopicLinkBD).where(ExerciseTopicLinkBD.exercise_id.in_(used_ids), ExerciseTopicLinkBD.topic_id.in_(topic_ids)))
    await db.execute(delete(ExerciseTaskLinkBD).where(ExerciseTaskLinkBD.exercise_id.in_(used_ids), ExerciseTaskLinkBD.exam_task_id.in_(task_ids)))
    db.add_all([ExerciseTopicLinkBD(exercise_id=exercise.id, topic_id=topic["topicId"], is_primary=True) for topic, _, exercise, _ in plans])
    db.add_all([ExerciseTaskLinkBD(exercise_id=exercise.id, exam_task_id=task_by_number[topic["taskNumber"]], is_primary=True)
                for topic, _, exercise, _ in plans])
    await db.flush()

    canonical_ids = set()
    async def publish_set(task_number, topic_id, title, members):
        task_id = task_by_number[task_number]
        options = sorted([item for item in sets if item.exam_task_id == task_id and item.topic_id == topic_id], key=lambda item: (0 if (item.configuration or {}).get("scopeRole") == ("topic" if topic_id else "task") else 1, item.id))
        target = options[0] if options else ExerciseSetBD(course_version_id=course_id, exam_task_id=task_id, topic_id=topic_id, title=title, access_level="free", configuration={}, selection_strategy="least_seen_random", status="published")
        if not options:
            db.add(target); await db.flush(); sets.append(target); counters["setsCreated"] += 1
        canonical_ids.add(target.id)
        target.title = title
        target.status = "published"
        target.configuration = {**_scope_config(target.configuration, role="topic" if topic_id else "task", code=f"topic:{topic_id}" if topic_id else f"task:{task_id}", generated=False), "curatedRevision": package["revision"], "reviewedBank": "task10-11"}
        await _sync_membership(db, target, members)
        await db.flush()
        if target.configuration.get("demoSelectionMode") != "manual":
            await sync_preview_membership(db, target)
    for topic in package["after"]["topics"]:
        await publish_set(topic["taskNumber"], topic["topicId"], topic["title"], {exercise.id for t, _, exercise, _ in plans if t["topicId"] == topic["topicId"]})
    for number in [10, 11]:
        unique = {}
        for topic, card, exercise, _ in plans:
            if topic["taskNumber"] == number:
                unique.setdefault(word_key(card["lexeme"]), exercise.id)
        await publish_set(number, None, "Смешанная практика", set(unique.values()))
    for target in sets:
        if target.id not in canonical_ids:
            target.status = "archived"
    await db.commit()
    return {"summary": summary(package), "changes": counters}
