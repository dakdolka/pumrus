"""Publish the reviewed authorial practice expansion and safe data repairs.

The command is a dry run by default. Repeated execution is idempotent: every
authored exercise has a stable key, and repaired legacy rows receive a new
version instead of being edited in place.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.infra.catalog.models import ExamTaskBD, TopicBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
)
from app.scripts.curated_practice_expansion import (
    PRACTICE_REFERENCES,
    PRACTICE_REVISION,
    PRACTICE_SETS,
)
from app.scripts.publish_curated_theory import _course_version
from app.scripts.practice_scope_sync import sync_practice_scopes


LEGACY_SET_TITLES = {
    (10, "Пре/При"): "ПРЕ- и ПРИ-",
    (11, "11..."): "Суффиксы",
    (18, "18 Запоминалка"): "Вводные слова: памятка",
}

STRESS_YO_REPAIRS = {
    "договорЕнность": "договорЁнность",
    "свЕкла": "свЁкла",
    "шофЕр": "шофЁр",
    "щЕлкать": "щЁлкать",
    "довезЕнный": "довезЁнный",
    "заселЕнный": "заселЁнный",
    "низведЕнный": "низведЁнный",
    "облегчЕнный": "облегчЁнный",
    "ободрЕнный": "ободрЁнный",
    "обострЕнный": "обострЁнный",
    "отключЕнный": "отключЁнный",
    "повторЕнный": "повторЁнный",
    "поделЕнный": "поделЁнный",
    "приручЕнный": "приручЁнный",
    "углублЕнный": "углублЁнный",
}

TEXT_REPAIRS = {
    "ученики аккомпаниру_т": (
        "ученики аккомпаниру_т",
        "ученики аккомпанируют",
    ),
    "пристутству_т": (
        "присутству_т",
        "присутствует",
    ),
}

TOPIC_CODE_ALIASES = {
    "task-7-nouns-complete-2026": "task-7-nouns",
    "task-7-numerals-complete-2026": "task-7-numerals",
    "task-7-verbs-complete-2026": "task-7-verbs",
    "task-7-participles-complete-2026": "task-7-participles",
    "task-9-checkable-complete-2026": "task-9-checkable",
    "task-10-exceptions-complete-2026": "task-10-invariable",
    "task-14-adverbs-complete-2026": "task-14-adverbs",
    "task-14-particles-complete-2026": "task-14-particles",
    "legacy-theory-9": "task-9-alternating",
    "legacy-theory-4": "task-10-zs",
    "legacy-theory-30": "task-10-invariable",
    "legacy-theory-6": "task-10-signs",
    "legacy-theory-7": "task-10-signs",
    "legacy-theory-8": "task-10-pre-pri",
}


def _payload(item: dict[str, Any], key: str) -> dict[str, Any]:
    answer_value = item["answer"]
    feedback = {
        "correctAnswer": (
            ", ".join(str(value) for value in answer_value)
            if isinstance(answer_value, list)
            else answer_value
        ),
        "correct": item["explanation"],
        "incorrect": item["explanation"],
    }
    marker = {
        "curatedKey": key,
        "curatedRevision": PRACTICE_REVISION,
        "sourceReferences": PRACTICE_REFERENCES,
    }
    if item["type"] == "single_choice":
        options = [
            {"key": f"option-{index}", "label": label}
            for index, label in enumerate(item["options"])
        ]
        correct_key = next(
            option["key"] for option in options
            if option["label"] == item["answer"]
        )
        return {
            "interaction_type": "single_choice",
            "prompt_data": {"content": item["prompt"], "format": "plain_text"},
            "interaction_config": {"options": options},
            "answer_config": {"correctOptionKey": correct_key},
            "checker_type": "exact_option",
            "checker_config": marker,
            "feedback_data": feedback,
        }
    if item["type"] == "multiple_choice":
        options = [
            {"key": f"option-{index}", "label": label}
            for index, label in enumerate(item["options"])
        ]
        answers = {str(value) for value in item["answer"]}
        correct_keys = [
            option["key"] for option in options
            if option["label"] in answers
        ]
        if len(correct_keys) != len(answers):
            raise RuntimeError(
                f"Multiple-choice answer is not present in options: {item!r}"
            )
        return {
            "interaction_type": "multiple_choice",
            "prompt_data": {"content": item["prompt"], "format": "plain_text"},
            "interaction_config": {"options": options},
            "answer_config": {"correctOptionKeys": correct_keys},
            "checker_type": "set_equality",
            "checker_config": marker,
            "feedback_data": feedback,
        }
    return {
        "interaction_type": "vowel_fill",
        "prompt_data": {"content": item["prompt"], "format": "plain_text"},
        "interaction_config": {
            "variant": "masked_letters",
            "mask": item["prompt"],
        },
        "answer_config": {"acceptedAnswers": [item["answer"]]},
        "checker_type": "normalized_text",
        "checker_config": {
            **marker,
            "trim": True,
            "caseInsensitive": True,
            "yoPolicy": "distinct",
        },
        "feedback_data": feedback,
    }


async def _topic_by_code(
    session: AsyncSession,
    course_version_id: int,
    code: str | None,
) -> TopicBD | None:
    if not code:
        return None
    code = TOPIC_CODE_ALIASES.get(code, code)
    return await session.scalar(
        select(TopicBD).where(
            TopicBD.course_version_id == course_version_id,
            TopicBD.code == code,
        )
    )


async def _ensure_set(
    session: AsyncSession,
    course_version_id: int,
    task: ExamTaskBD,
    definition: dict[str, Any],
) -> tuple[ExerciseSetBD, bool]:
    curated_code = definition["code"]
    candidates = list((await session.scalars(
        select(ExerciseSetBD).where(
            ExerciseSetBD.course_version_id == course_version_id,
            ExerciseSetBD.exam_task_id == task.id,
        )
    )).all())
    exercise_set = next(
        (
            item for item in candidates
            if (item.configuration or {}).get("curatedCode") == curated_code
        ),
        None,
    )
    if exercise_set is None and definition.get("reuse_existing_title"):
        exercise_set = next(
            (
                item for item in candidates
                if item.title == definition["title"]
                and not (item.configuration or {}).get("curatedCode")
            ),
            None,
        )
    created = exercise_set is None
    if exercise_set is None:
        exercise_set = ExerciseSetBD(
            course_version_id=course_version_id,
            exam_task_id=task.id,
            topic_id=None,
            title=definition["title"],
            selection_strategy="least_seen_random",
            configuration={
                "sessionSize": 50,
                "pageSize": 5,
                "curatedCode": curated_code,
                "curatedRevision": PRACTICE_REVISION,
            },
            status="published",
        )
        session.add(exercise_set)
        await session.flush()
    else:
        # Preserve editorial title/status/settings after the first publication.
        exercise_set.configuration = {
            **(exercise_set.configuration or {}),
            "curatedCode": curated_code,
            "curatedRevision": PRACTICE_REVISION,
        }
    return exercise_set, created


async def _published_keys(
    session: AsyncSession,
    exercise_set_id: int,
) -> dict[str, ExerciseBD]:
    rows = (await session.execute(
        select(ExerciseBD, ExerciseVersionBD)
        .join(
            ExerciseSetItemBD,
            ExerciseSetItemBD.exercise_id == ExerciseBD.id,
        )
        .join(
            ExerciseVersionBD,
            ExerciseVersionBD.id == ExerciseBD.published_version_id,
        )
        .where(ExerciseSetItemBD.exercise_set_id == exercise_set_id)
    )).all()
    return {
        str(version.checker_config.get("curatedKey")): exercise
        for exercise, version in rows
        if version.checker_config.get("curatedKey")
    }


async def _next_version_number(
    session: AsyncSession,
    exercise_id: int,
) -> int:
    current = await session.scalar(
        select(func.max(ExerciseVersionBD.version_number)).where(
            ExerciseVersionBD.exercise_id == exercise_id
        )
    )
    return int(current or 0) + 1


async def _publish_version(
    session: AsyncSession,
    exercise: ExerciseBD,
    payload: dict[str, Any],
    now: datetime,
) -> ExerciseVersionBD:
    if exercise.published_version_id is not None:
        previous = await session.get(ExerciseVersionBD, exercise.published_version_id)
        if previous is not None and previous.status == "published":
            previous.status = "archived"
    version = ExerciseVersionBD(
        exercise_id=exercise.id,
        version_number=await _next_version_number(session, exercise.id),
        status="published",
        interaction_type=payload["interaction_type"],
        response_schema_version=1,
        prompt_data=payload["prompt_data"],
        interaction_config=payload["interaction_config"],
        answer_config=payload["answer_config"],
        checker_type=payload["checker_type"],
        checker_config=payload["checker_config"],
        feedback_data=payload["feedback_data"],
        published_at=now,
    )
    session.add(version)
    await session.flush()
    exercise.status = "published"
    exercise.published_version_id = version.id
    return version


async def _publish_sets(
    session: AsyncSession,
    course_version_id: int,
    tasks_by_number: dict[int, ExamTaskBD],
    counters: dict[str, int],
    now: datetime,
) -> None:
    for definition in PRACTICE_SETS:
        task = tasks_by_number.get(definition["task_number"])
        if task is None:
            counters["tasks_missing"] += 1
            continue
        exercise_set, created = await _ensure_set(
            session, course_version_id, task, definition
        )
        counters["sets_created"] += int(created)
        existing = await _published_keys(session, exercise_set.id)
        last_order = await session.scalar(
            select(func.max(ExerciseSetItemBD.sort_order)).where(
                ExerciseSetItemBD.exercise_set_id == exercise_set.id
            )
        )
        next_order = int(last_order if last_order is not None else -1) + 1
        for index, item in enumerate(definition["items"]):
            key = f"{definition['code']}:{index + 1:03d}"
            if key in existing:
                published = await session.get(
                    ExerciseVersionBD, existing[key].published_version_id
                )
                if (
                    published is not None
                    and published.checker_config.get("curatedRevision")
                    == PRACTICE_REVISION
                ):
                    counters["exercises_unchanged"] += 1
                    continue
                exercise = existing[key]
            else:
                exercise = ExerciseBD(
                    course_version_id=course_version_id,
                    status="published",
                    source=f"umrus_original:{definition['code']}",
                )
                session.add(exercise)
                await session.flush()
                session.add(ExerciseTaskLinkBD(
                    exercise_id=exercise.id,
                    exam_task_id=task.id,
                    is_primary=True,
                ))
                session.add(ExerciseSetItemBD(
                    exercise_set_id=exercise_set.id,
                    exercise_id=exercise.id,
                    sort_order=next_order,
                ))
                next_order += 1
            await _publish_version(session, exercise, _payload(item, key), now)
            topic = await _topic_by_code(
                session, course_version_id, item.get("topic_code")
            )
            if item.get("topic_code") and topic is None:
                counters["topic_links_missing"] += 1
            elif topic is not None:
                links = list((await session.scalars(
                    select(ExerciseTopicLinkBD).where(
                        ExerciseTopicLinkBD.exercise_id == exercise.id
                    )
                )).all())
                link = next(
                    (candidate for candidate in links if candidate.topic_id == topic.id),
                    None,
                )
                for candidate in links:
                    candidate.is_primary = candidate.topic_id == topic.id
                if link is None:
                    session.add(ExerciseTopicLinkBD(
                        exercise_id=exercise.id,
                        topic_id=topic.id,
                        is_primary=True,
                    ))
                else:
                    link.is_primary = True
            counters["exercises_published"] += 1


async def _rename_legacy_sets(
    session: AsyncSession,
    tasks_by_number: dict[int, ExamTaskBD],
) -> int:
    changed = 0
    for (number, old_title), new_title in LEGACY_SET_TITLES.items():
        task = tasks_by_number.get(number)
        if task is None:
            continue
        item = await session.scalar(select(ExerciseSetBD).where(
            ExerciseSetBD.exam_task_id == task.id,
            ExerciseSetBD.title == old_title,
        ))
        if item is not None:
            item.title = new_title
            changed += 1
    return changed


def _stress_payload(version: ExerciseVersionBD, corrected: str) -> dict[str, Any]:
    word = corrected.casefold()
    stressed = next(
        index for index, character in enumerate(corrected)
        if character in "АЕЁИОУЫЭЮЯ"
    )
    checker = deepcopy(version.checker_config or {})
    checker["curatedRepair"] = PRACTICE_REVISION
    prompt = deepcopy(version.prompt_data or {})
    prompt.update({"content": word, "word": word, "legacyRaw": corrected})
    feedback = deepcopy(version.feedback_data or {})
    feedback["correctAnswer"] = corrected
    return {
        "interaction_type": "stress_selection",
        "prompt_data": prompt,
        "interaction_config": {
            "selectablePositions": [
                index for index, character in enumerate(word)
                if character in "аеёиоуыэюя"
            ]
        },
        "answer_config": {"correctCharacterIndex": stressed},
        "checker_type": "exact_position",
        "checker_config": checker,
        "feedback_data": feedback,
    }


def _text_repair_payload(
    version: ExerciseVersionBD,
    mask: str,
    answer: str,
) -> dict[str, Any]:
    checker = deepcopy(version.checker_config or {})
    checker["curatedRepair"] = PRACTICE_REVISION
    prompt = deepcopy(version.prompt_data or {})
    prompt.update({"content": mask, "legacyRaw": answer})
    interaction = deepcopy(version.interaction_config or {})
    interaction["mask"] = mask
    feedback = deepcopy(version.feedback_data or {})
    feedback["correctAnswer"] = answer
    return {
        "interaction_type": version.interaction_type,
        "prompt_data": prompt,
        "interaction_config": interaction,
        "answer_config": {"acceptedAnswers": [answer]},
        "checker_type": version.checker_type,
        "checker_config": checker,
        "feedback_data": feedback,
    }


async def _repair_legacy_data(
    session: AsyncSession,
    tasks_by_number: dict[int, ExamTaskBD],
    counters: dict[str, int],
    now: datetime,
) -> None:
    for task_number in (4, 12):
        task = tasks_by_number.get(task_number)
        if task is None:
            continue
        rows = (await session.execute(
            select(ExerciseBD, ExerciseVersionBD)
            .join(
                ExerciseTaskLinkBD,
                ExerciseTaskLinkBD.exercise_id == ExerciseBD.id,
            )
            .join(
                ExerciseVersionBD,
                ExerciseVersionBD.id == ExerciseBD.published_version_id,
            )
            .where(ExerciseTaskLinkBD.exam_task_id == task.id)
        )).all()
        for exercise, version in rows:
            if version.checker_config.get("curatedRepair") == PRACTICE_REVISION:
                counters["repairs_unchanged"] += 1
                continue
            if task_number == 4:
                raw = str(version.prompt_data.get("legacyRaw") or "")
                corrected = STRESS_YO_REPAIRS.get(raw)
                if corrected:
                    await _publish_version(
                        session, exercise, _stress_payload(version, corrected), now
                    )
                    counters["repairs_published"] += 1
            else:
                content = str(version.prompt_data.get("content") or "")
                repair = TEXT_REPAIRS.get(content)
                if repair:
                    await _publish_version(
                        session,
                        exercise,
                        _text_repair_payload(version, *repair),
                        now,
                    )
                    counters["repairs_published"] += 1


async def publish(course_version_code: str | None, execute: bool) -> None:
    async with async_session_factory() as session:
        course_version = await _course_version(session, course_version_code)
        tasks = list((await session.scalars(select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == course_version.id
        ))).all())
        tasks_by_number = {task.number: task for task in tasks}
        counters = {
            "sets_created": 0,
            "exercises_published": 0,
            "exercises_unchanged": 0,
            "topic_links_missing": 0,
            "tasks_missing": 0,
            "legacy_sets_renamed": 0,
            "repairs_published": 0,
            "repairs_unchanged": 0,
        }
        now = datetime.now(timezone.utc)
        await _publish_sets(
            session, course_version.id, tasks_by_number, counters, now
        )
        counters["legacy_sets_renamed"] = await _rename_legacy_sets(
            session, tasks_by_number
        )
        await _repair_legacy_data(session, tasks_by_number, counters, now)
        counters.update(
            await sync_practice_scopes(session, course_version.id)
        )

        print("Curated practice expansion plan:")
        print(f"  course version: {course_version.code}")
        for key, value in counters.items():
            print(f"  {key.replace('_', ' ')}: {value}")
        if execute:
            await session.commit()
            print("Curated practice expansion published successfully.")
        else:
            await session.rollback()
            print("Dry run completed. No practice records were written.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-version")
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    asyncio.run(publish(arguments.course_version, arguments.execute))


if __name__ == "__main__":
    main()
