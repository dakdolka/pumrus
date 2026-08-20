"""Build navigable task/topic practice scopes without duplicating exercises."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.catalog.models import ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
)


SCOPE_REVISION = "practice-scopes-2026-v1"
PUBLIC_ROLE_TASK = "task"
PUBLIC_ROLE_TOPIC = "topic"
HIDDEN_ROLE_SOURCE = "source"


def _normalise(value: Any) -> str:
    return str(value or "").strip().casefold().replace("ё", "е")


def _stress_topic_words() -> dict[str, str]:
    source = (
        Path(__file__).parents[1]
        / "core"
        / "tasks"
        / "parsers"
        / "data"
        / "stressWords.json"
    )
    words = [_normalise(value) for value in json.loads(source.read_text(encoding="utf-8"))]
    result: dict[str, str] = {}
    for word in words[:63]:
        result[word] = "task-4-nouns"
    result[words[1]] = "task-4-adjectives"
    for word in words[63:74]:
        result[word] = "task-4-adjectives"
    for word in words[74:164]:
        result[word] = "task-4-verbs"
    for word in words[164:198]:
        result[word] = "task-4-participles"
    for word in words[198:]:
        result[word] = "task-4-adjectives"
    return result


STRESS_TOPIC_WORDS = _stress_topic_words()
TASK11_ADVERBS = {
    "слева", "досыта", "издавна", "вправо", "наутро", "запросто", "нипочем",
    "въявь",
}


def _version_text(version: ExerciseVersionBD) -> tuple[str, str]:
    prompt = str((version.prompt_data or {}).get("content") or "")
    answer = str((version.feedback_data or {}).get("correctAnswer") or "")
    if not answer:
        accepted = (version.answer_config or {}).get("acceptedAnswers") or []
        answer = str(accepted[0]) if accepted else ""
    return prompt, answer


def infer_topic_code(task_number: int, version: ExerciseVersionBD) -> str | None:
    """Return a conservative topic for legacy rows that lost their topic link."""
    prompt, answer = _version_text(version)
    clean_answer = _normalise(answer)
    first_word = re.split(r"\s+", clean_answer, maxsplit=1)[0].strip(".,!?:;()[]«»\"")

    if task_number == 4:
        known = STRESS_TOPIC_WORDS.get(first_word)
        if known:
            return known
        if first_word.endswith(("но", "ко", "ло")):
            return "task-4-adjectives"
        if first_word.endswith(("ть", "ться", "ла", "лась", "лит", "лят")):
            return "task-4-verbs"
        if first_word.endswith(("нный", "нная", "нный", "вший", "вшись")):
            return "task-4-participles"
        return "task-4-nouns"

    if task_number == 11:
        if first_word in TASK11_ADVERBS:
            return "legacy-theory-24"
        if re.search(
            r"(ть|ться|вать|ваться|вают|вает|лись|вший|вшая|ющий|ющая|ющее|ющие)$",
            first_word,
        ):
            return "legacy-theory-23"
        if re.search(
            r"(ый|ий|ой|ая|яя|ое|ее|ые|ие|ого|ему|ую|ых|ым|им|ский|ская|ское|"
            r"нный|нная|нное|чий|чая|чее)$",
            first_word,
        ):
            return "legacy-theory-25"
        return "legacy-theory-26"

    if task_number == 12:
        return "task-12-conjugation"

    if task_number == 13:
        return "legacy-theory-22"

    if task_number == 14:
        lowered = _normalise(prompt)
        preposition_markers = (
            "(в)виду", "иметь (в)виду", "(в)место", "(в)следств", "(на)подоб",
            "(на)счет", "(в)след", "(на)встреч", "(в)связ", "(в)отлич", "(в)целях",
            "(в)силу", "(в)мерах", "(в)течение", "(в)продолжение", "(на)протяжении",
            "(в)заключение", "(в)результате", "(за)исключением", "(за)неимением",
            "(за)счет", "(по)причине", "(в)роде", "согласовать (в)роде",
        )
        conjunction_markers = (
            "(что)бы", "(то)же", "то(же)", "(так)же", "так(же)", "при(чем)",
            "(при)чем", "при(том)", "(за)то", "(за)чем", "(от)чего", "по(тому)",
            "(по)чем", "и(так)",
        )
        if any(marker in lowered for marker in preposition_markers):
            return "task-14-prepositions"
        if any(marker in lowered for marker in conjunction_markers):
            return "legacy-theory-29"
        if any(marker in lowered for marker in ("(пол)", "(полу)", "(в)(пол)")):
            return "task-14-complex-words"
        if any(marker in lowered for marker in ("как(будто)", "(как)раз", "(вряд)ли", "(все)равно")):
            return "task-14-particles"
        return "task-14-adverbs"

    if task_number == 15:
        return "task-15-context"

    if task_number == 18:
        return "task-18-introductory-meaning"

    return None


def _scope_config(
    original: dict[str, Any] | None,
    *,
    role: str,
    code: str,
    generated: bool,
) -> dict[str, Any]:
    return {
        **(original or {}),
        "sessionSize": int((original or {}).get("sessionSize", 50)),
        "pageSize": int((original or {}).get("pageSize", 5)),
        "scopeRole": role,
        "scopeCode": code,
        "scopeRevision": SCOPE_REVISION,
        "scopeGenerated": generated,
        "guestAccessible": True,
    }


async def _sync_membership(
    session: AsyncSession,
    exercise_set: ExerciseSetBD,
    target_ids: set[int],
) -> tuple[int, int]:
    rows = list((await session.scalars(
        select(ExerciseSetItemBD).where(
            ExerciseSetItemBD.exercise_set_id == exercise_set.id
        )
    )).all())
    existing = {item.exercise_id: item for item in rows}
    removed = set(existing) - target_ids
    if removed:
        await session.execute(
            delete(ExerciseSetItemBD).where(
                ExerciseSetItemBD.exercise_set_id == exercise_set.id,
                ExerciseSetItemBD.exercise_id.in_(removed),
            )
        )
    added = target_ids - set(existing)
    next_order = max((item.sort_order for item in rows), default=-1) + 1
    for exercise_id in sorted(added):
        session.add(ExerciseSetItemBD(
            exercise_set_id=exercise_set.id,
            exercise_id=exercise_id,
            sort_order=next_order,
        ))
        next_order += 1
    return len(added), len(removed)


async def sync_practice_scopes(
    session: AsyncSession,
    course_version_id: int,
) -> dict[str, int]:
    stats = {
        "topic_links_inferred": 0,
        "topic_links_unresolved": 0,
        "scope_sets_created": 0,
        "scope_sets_updated": 0,
        "scope_items_added": 0,
        "scope_items_removed": 0,
    }
    tasks = list((await session.scalars(
        select(ExamTaskBD).where(ExamTaskBD.course_version_id == course_version_id)
    )).all())
    task_by_id = {task.id: task for task in tasks}
    topic_rows = (await session.execute(
        select(TopicBD, ExamTaskTopicBD.exam_task_id)
        .join(ExamTaskTopicBD, ExamTaskTopicBD.topic_id == TopicBD.id)
        .where(TopicBD.course_version_id == course_version_id)
    )).all()
    topic_by_id = {topic.id: topic for topic, _ in topic_rows}
    task_id_by_topic_id = {topic.id: task_id for topic, task_id in topic_rows}
    topic_by_task_code = {
        (task_id, topic.code): topic
        for topic, task_id in topic_rows
    }

    sets = list((await session.scalars(
        select(ExerciseSetBD).where(
            ExerciseSetBD.course_version_id == course_version_id,
            ExerciseSetBD.status == "published",
        )
    )).all())
    set_by_id = {item.id: item for item in sets}
    set_items = list((await session.scalars(
        select(ExerciseSetItemBD).where(
            ExerciseSetItemBD.exercise_set_id.in_(set_by_id)
        )
    )).all()) if set_by_id else []
    item_ids_by_set: dict[int, set[int]] = {item.id: set() for item in sets}
    for item in set_items:
        item_ids_by_set[item.exercise_set_id].add(item.exercise_id)
    eligible_ids = {item.exercise_id for item in set_items}
    if not eligible_ids:
        return stats

    exercise_rows = (await session.execute(
        select(ExerciseBD, ExerciseVersionBD)
        .join(
            ExerciseVersionBD,
            ExerciseVersionBD.id == ExerciseBD.published_version_id,
        )
        .where(
            ExerciseBD.id.in_(eligible_ids),
            ExerciseBD.status == "published",
        )
    )).all()
    version_by_exercise = {exercise.id: version for exercise, version in exercise_rows}
    eligible_ids &= set(version_by_exercise)

    task_links = list((await session.scalars(
        select(ExerciseTaskLinkBD).where(
            ExerciseTaskLinkBD.exercise_id.in_(eligible_ids)
        )
    )).all())
    task_ids_by_exercise: dict[int, set[int]] = {}
    exercise_ids_by_task: dict[int, set[int]] = {}
    for link in task_links:
        task_ids_by_exercise.setdefault(link.exercise_id, set()).add(link.exam_task_id)
        exercise_ids_by_task.setdefault(link.exam_task_id, set()).add(link.exercise_id)

    topic_links = list((await session.scalars(
        select(ExerciseTopicLinkBD).where(
            ExerciseTopicLinkBD.exercise_id.in_(eligible_ids)
        )
    )).all())
    topic_ids_by_exercise: dict[int, set[int]] = {}
    for link in topic_links:
        topic_ids_by_exercise.setdefault(link.exercise_id, set()).add(link.topic_id)

    for exercise_id in sorted(eligible_ids):
        if topic_ids_by_exercise.get(exercise_id):
            continue
        for task_id in task_ids_by_exercise.get(exercise_id, ()):
            task = task_by_id.get(task_id)
            if task is None:
                continue
            code = infer_topic_code(task.number, version_by_exercise[exercise_id])
            topic = topic_by_task_code.get((task_id, code)) if code else None
            if topic is None:
                stats["topic_links_unresolved"] += 1
                continue
            session.add(ExerciseTopicLinkBD(
                exercise_id=exercise_id,
                topic_id=topic.id,
                is_primary=True,
            ))
            topic_ids_by_exercise.setdefault(exercise_id, set()).add(topic.id)
            stats["topic_links_inferred"] += 1
            break
    await session.flush()

    # A legacy/curated set that contains one topic only is already the best
    # canonical topic set; retain its id so saved theory links keep working.
    for exercise_set in sets:
        if exercise_set.topic_id is not None:
            exercise_set.configuration = _scope_config(
                exercise_set.configuration,
                role=PUBLIC_ROLE_TOPIC,
                code=f"topic:{exercise_set.topic_id}",
                generated=bool((exercise_set.configuration or {}).get("scopeGenerated")),
            )
            continue
        if (exercise_set.configuration or {}).get("scopeRole"):
            continue
        ids = item_ids_by_set.get(exercise_set.id, set()) & eligible_ids
        if not ids:
            continue
        common: set[int] | None = None
        for exercise_id in ids:
            linked = topic_ids_by_exercise.get(exercise_id, set())
            common = set(linked) if common is None else common & linked
        valid = {
            topic_id for topic_id in (common or set())
            if topic_id in topic_by_id
            and task_id_by_topic_id.get(topic_id) == exercise_set.exam_task_id
        }
        if len(valid) == 1:
            exercise_set.topic_id = valid.pop()
            exercise_set.configuration = _scope_config(
                exercise_set.configuration,
                role=PUBLIC_ROLE_TOPIC,
                code=f"topic:{exercise_set.topic_id}",
                generated=False,
            )

    async def ensure_scope_set(
        *,
        task: ExamTaskBD,
        topic: TopicBD | None,
        target_ids: set[int],
    ) -> ExerciseSetBD:
        role = PUBLIC_ROLE_TOPIC if topic else PUBLIC_ROLE_TASK
        code = f"topic:{topic.id}" if topic else f"task:{task.id}"
        candidates = [
            item for item in sets
            if item.exam_task_id == task.id and item.topic_id == (topic.id if topic else None)
        ]
        exact = next(
            (item for item in candidates if item_ids_by_set.get(item.id, set()) == target_ids),
            None,
        )
        scoped = next(
            (
                item for item in candidates
                if (item.configuration or {}).get("scopeCode") == code
            ),
            None,
        )
        selected = exact or scoped
        if selected is None:
            selected = ExerciseSetBD(
                course_version_id=course_version_id,
                exam_task_id=task.id,
                topic_id=topic.id if topic else None,
                title=topic.title if topic else "Смешанная практика",
                selection_strategy="least_seen_random",
                configuration={},
                status="published",
            )
            session.add(selected)
            await session.flush()
            sets.append(selected)
            set_by_id[selected.id] = selected
            item_ids_by_set[selected.id] = set()
            stats["scope_sets_created"] += 1
        generated = selected is not exact or bool(
            (selected.configuration or {}).get("scopeGenerated")
        )
        selected.selection_strategy = "least_seen_random"
        selected.configuration = _scope_config(
            selected.configuration,
            role=role,
            code=code,
            generated=generated,
        )
        added, removed = await _sync_membership(session, selected, target_ids)
        if added or removed:
            stats["scope_sets_updated"] += 1
            stats["scope_items_added"] += added
            stats["scope_items_removed"] += removed
            item_ids_by_set[selected.id] = set(target_ids)
        for duplicate in candidates:
            if duplicate.id == selected.id:
                continue
            duplicate.configuration = _scope_config(
                duplicate.configuration,
                role=HIDDEN_ROLE_SOURCE,
                code=f"source:{duplicate.id}",
                generated=False,
            )
        return selected

    for task in tasks:
        task_ids = exercise_ids_by_task.get(task.id, set()) & eligible_ids
        if not task_ids:
            continue
        await ensure_scope_set(task=task, topic=None, target_ids=task_ids)
        topics_for_task = [topic for topic, task_id in topic_rows if task_id == task.id]
        for topic in topics_for_task:
            topic_ids = {
                exercise_id for exercise_id in task_ids
                if topic.id in topic_ids_by_exercise.get(exercise_id, set())
            }
            if topic_ids:
                await ensure_scope_set(task=task, topic=topic, target_ids=topic_ids)

    return stats
