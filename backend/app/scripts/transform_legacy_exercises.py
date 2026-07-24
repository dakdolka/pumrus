"""Transform confirmed legacy trainers into the versioned exercise bank."""

from __future__ import annotations

import argparse
import asyncio
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, TopicBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
    TaskDocumentBD,
)


VOWELS = frozenset("аеёиоуыэюя")

# Only mappings explicitly confirmed during the architecture review belong here.
# Matching is conservative: an unknown trainer blocks execution.
CONFIRMED_TASK_RULES = (
    (("пре", "при"), 10, "Пре/при"),
    (("ударен",), 4, None),
    (("гласн", "глагол"), 12, None),
    (("11", "задан"), 11, None),
    (("словарн", "слов"), 9, "Словарные слова"),
    (("14", "задан"), 14, None),
    (("18", "запоминал"), 18, None),
)


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower().replace("ё", "е"))


def _scope_for_task(name: str) -> tuple[int, str | None] | None:
    normalised = _normalise(name)
    # The confirmed legacy task 11 is named simply "11..." in the source DB.
    if re.match(r"^11(?:\D|$)", normalised):
        return 11, None
    for needles, task_number, topic_title in CONFIRMED_TASK_RULES:
        if all(needle in normalised for needle in needles):
            return task_number, topic_title
    return None


def _stress_position(correct: str) -> int | None:
    positions = [
        index
        for index, character in enumerate(correct)
        if character.isalpha()
        and character == character.upper()
        and character != character.lower()
    ]
    return positions[0] if len(positions) == 1 else None


def _is_empty_item(item: dict[str, Any]) -> bool:
    return not any(
        str(item.get(field) or "").strip()
        for field in ("content_raw", "content_visible", "content_correct")
    )


def _convert_item(
    task: dict[str, Any],
    item: dict[str, Any],
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    trainer_type = str(task["trainer_type"])
    visible = item["content_visible"]
    correct = item["content_correct"]
    feedback = {
        "correctAnswer": correct,
        "correct": item["notice_right"],
        "incorrect": item["notice_wrong"],
    }
    prompt = {
        "content": visible,
        "format": "legacy_html",
        "legacyRaw": item["content_raw"],
    }

    if trainer_type == "options":
        if not options:
            raise ValueError("options trainer has no options")
        correct_option_id = item["correct_option_fk"]
        option_keys = [f"legacy-option-{option['id']}" for option in options]
        correct_key = (
            f"legacy-option-{correct_option_id}"
            if correct_option_id is not None
            else None
        )
        if correct_key not in option_keys:
            matching = [
                option
                for option in options
                if _normalise(option["content"]) == _normalise(correct)
            ]
            if len(matching) != 1:
                raise ValueError("correct option cannot be resolved")
            correct_key = f"legacy-option-{matching[0]['id']}"
        return {
            "interaction_type": "single_choice",
            "prompt_data": prompt,
            "interaction_config": {
                "options": [
                    {
                        "key": f"legacy-option-{option['id']}",
                        "label": option["content"],
                        "extras": option["extras"],
                    }
                    for option in options
                ]
            },
            "answer_config": {"correctOptionKey": correct_key},
            "checker_type": "exact_option",
            "checker_config": {},
            "feedback_data": feedback,
        }

    if trainer_type == "stress":
        correct_position = _stress_position(correct)
        if correct_position is None:
            raise ValueError("stress position cannot be resolved")
        selectable = [
            index
            for index, character in enumerate(visible.lower())
            if character in VOWELS
        ]
        if correct_position not in selectable:
            raise ValueError("stress position is not a selectable vowel")
        return {
            "interaction_type": "stress_selection",
            "prompt_data": {**prompt, "word": visible},
            "interaction_config": {"selectablePositions": selectable},
            "answer_config": {"correctCharacterIndex": correct_position},
            "checker_type": "exact_position",
            "checker_config": {},
            "feedback_data": feedback,
        }

    if trainer_type == "dictionary":
        return {
            "interaction_type": "text_input",
            "prompt_data": prompt,
            "interaction_config": {
                "variant": "masked_letters",
                "mask": visible,
            },
            "answer_config": {"acceptedAnswers": [correct]},
            "checker_type": "normalized_text",
            "checker_config": {
                "trim": True,
                "caseInsensitive": True,
                "yoPolicy": "distinct",
            },
            "feedback_data": feedback,
        }

    if trainer_type == "input":
        return {
            "interaction_type": "text_input",
            "prompt_data": prompt,
            "interaction_config": {},
            "answer_config": {"acceptedAnswers": [correct]},
            "checker_type": "normalized_text",
            "checker_config": {
                "trim": True,
                "caseInsensitive": True,
                "yoPolicy": "distinct",
            },
            "feedback_data": feedback,
        }

    raise ValueError(f"unsupported trainer type: {trainer_type}")


async def _load_legacy(
    session: AsyncSession,
) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    tasks = [
        dict(row)
        for row in (
            await session.execute(
                text(
                    """
                    SELECT id, name, trainer_type, default_option_set_fk
                    FROM task
                    ORDER BY id
                    """
                )
            )
        ).mappings()
    ]
    items = [
        dict(row)
        for row in (
            await session.execute(
                text(
                    """
                    SELECT id, task_id, content_raw, content_visible,
                           content_correct, correct_option_fk,
                           option_set_override_fk, notice_wrong, notice_right
                    FROM task_item
                    ORDER BY task_id, id
                    """
                )
            )
        ).mappings()
    ]
    items_by_task: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        items_by_task[item["task_id"]].append(item)
    return tasks, items_by_task


async def _options_for_item(
    session: AsyncSession,
    task: dict[str, Any],
    item: dict[str, Any],
) -> list[dict[str, Any]]:
    option_set_id = (
        item["option_set_override_fk"]
        if item["option_set_override_fk"] is not None
        else task["default_option_set_fk"]
    )
    if option_set_id is None:
        return []
    return [
        dict(row)
        for row in (
            await session.execute(
                text(
                    """
                    SELECT o.id, o.content, o.extras
                    FROM option_set2option link
                    JOIN option o ON o.id = link.option_id
                    WHERE link.option_set_id = :option_set_id
                    ORDER BY o.id
                    """
                ),
                {"option_set_id": option_set_id},
            )
        ).mappings()
    ]


async def _build_plan(
    session: AsyncSession,
    tasks: list[dict[str, Any]],
    items_by_task: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[str]]:
    plan: list[dict[str, Any]] = []
    problems: list[str] = []
    print("Exercise v2 transformation plan:")
    total_skipped_empty = 0
    for task in tasks:
        scope = _scope_for_task(task["name"])
        legacy_items = items_by_task[task["id"]]
        empty_items = [item for item in legacy_items if _is_empty_item(item)]
        importable_items = [item for item in legacy_items if not _is_empty_item(item)]
        item_count = len(importable_items)
        total_skipped_empty += len(empty_items)
        if scope is None:
            problems.append(
                f"legacy task {task['id']}: {task['name']} "
                f"({task['trainer_type']}, {len(legacy_items)} items) "
                "has no confirmed scope"
            )
            continue
        task_number, topic_title = scope
        invalid_items = 0
        for item in importable_items:
            try:
                options = await _options_for_item(session, task, item)
                _convert_item(task, item, options)
            except ValueError as error:
                invalid_items += 1
                problems.append(
                    f"task {task['id']} item {item['id']}: {error}; "
                    f"visible={item['content_visible']!r}; "
                    f"correct={item['content_correct']!r}"
                )
        plan.append(
            {
                "legacy_task": task,
                "task_number": task_number,
                "topic_title": topic_title,
                "item_count": item_count,
                "skipped_empty_count": len(empty_items),
                "invalid_items": invalid_items,
            }
        )
        topic_suffix = f", topic '{topic_title}'" if topic_title else ""
        skipped_suffix = (
            f", skipped empty={len(empty_items)}" if empty_items else ""
        )
        print(
            f"  trainer {task['id']}: {task['name']} "
            f"({task['trainer_type']}, {item_count} items) "
            f"-> task {task_number}{topic_suffix}{skipped_suffix}"
        )
    print(f"  trainers ready: {len(plan)}")
    print(f"  exercises ready: {sum(item['item_count'] for item in plan)}")
    print(f"  empty legacy items skipped: {total_skipped_empty}")
    print(f"  blocking problems: {len(problems)}")
    for problem in problems:
        print(f"  unresolved: {problem}")
    return plan, problems


async def _transform(
    session: AsyncSession,
    course_version: CourseVersionBD,
    plan: list[dict[str, Any]],
    items_by_task: dict[int, list[dict[str, Any]]],
) -> None:
    published_at = datetime.now(timezone.utc)
    task_documents: dict[int, TaskDocumentBD] = {}

    for entry in plan:
        legacy_task = entry["legacy_task"]
        exam_task = await session.scalar(
            select(ExamTaskBD).where(
                ExamTaskBD.course_version_id == course_version.id,
                ExamTaskBD.number == entry["task_number"],
            )
        )
        if exam_task is None:
            raise RuntimeError(f"Exam task {entry['task_number']} does not exist")

        topic = None
        if entry["topic_title"]:
            topic = await session.scalar(
                select(TopicBD).where(
                    TopicBD.course_version_id == course_version.id,
                    func.lower(TopicBD.title) == entry["topic_title"].lower(),
                )
            )
            if topic is None:
                raise RuntimeError(f"Topic '{entry['topic_title']}' does not exist")

        if exam_task.id not in task_documents:
            document = await session.scalar(
                select(TaskDocumentBD).where(TaskDocumentBD.exam_task_id == exam_task.id)
            )
            if document is None:
                document = TaskDocumentBD(
                    exam_task_id=exam_task.id,
                    title=f"Практика задания {exam_task.number}",
                    introduction={},
                    configuration={},
                    status="published",
                )
                session.add(document)
                await session.flush()
            task_documents[exam_task.id] = document

        exercise_set = ExerciseSetBD(
            course_version_id=course_version.id,
            exam_task_id=exam_task.id,
            topic_id=topic.id if topic else None,
            title=legacy_task["name"],
            selection_strategy="all_shuffled",
            configuration={"legacyTrainerType": str(legacy_task["trainer_type"])},
            status="published",
            source_legacy_task_id=legacy_task["id"],
        )
        session.add(exercise_set)
        await session.flush()

        converted_types: Counter[str] = Counter()
        importable_items = [
            item
            for item in items_by_task[legacy_task["id"]]
            if not _is_empty_item(item)
        ]
        for position, item in enumerate(importable_items, start=1):
            options = await _options_for_item(session, legacy_task, item)
            converted = _convert_item(legacy_task, item, options)
            converted_types[converted["interaction_type"]] += 1

            exercise = ExerciseBD(
                course_version_id=course_version.id,
                status="published",
                difficulty=None,
                source="legacy",
                source_legacy_task_item_id=item["id"],
            )
            session.add(exercise)
            await session.flush()

            version = ExerciseVersionBD(
                exercise_id=exercise.id,
                version_number=1,
                status="published",
                response_schema_version=1,
                source_legacy_task_item_id=item["id"],
                published_at=published_at,
                **converted,
            )
            session.add(version)
            await session.flush()
            exercise.published_version_id = version.id
            session.add(
                ExerciseTaskLinkBD(
                    exercise_id=exercise.id,
                    exam_task_id=exam_task.id,
                    is_primary=True,
                )
            )
            if topic is not None:
                session.add(
                    ExerciseTopicLinkBD(
                        exercise_id=exercise.id,
                        topic_id=topic.id,
                        is_primary=True,
                    )
                )
            session.add(
                ExerciseSetItemBD(
                    exercise_set_id=exercise_set.id,
                    exercise_id=exercise.id,
                    sort_order=position,
                    weight=1,
                )
            )

        summary = ", ".join(
            f"{name}={count}" for name, count in sorted(converted_types.items())
        )
        print(
            f"Migrated trainer {legacy_task['id']}: {legacy_task['name']} "
            f"({entry['item_count']} exercises; {summary})"
        )


async def transform(course_version_code: str, execute: bool) -> None:
    async with async_session_factory() as session:
        course_version = await session.scalar(
            select(CourseVersionBD).where(
                CourseVersionBD.code == course_version_code,
                CourseVersionBD.is_active.is_(True),
            )
        )
        if course_version is None:
            raise RuntimeError(
                f"Active course version '{course_version_code}' does not exist. "
                "Transform theory first."
            )

        tasks, items_by_task = await _load_legacy(session)
        plan, problems = await _build_plan(session, tasks, items_by_task)
        if problems:
            raise RuntimeError(
                "Exercise transformation is blocked. Resolve every item above "
                "before running with --execute."
            )

        if not execute:
            print("Dry run completed. No v2 records were written.")
            print("Run again with --execute to transform these exercises.")
            return

        migrated_count = await session.scalar(
            select(func.count(ExerciseBD.id)).where(
                ExerciseBD.source_legacy_task_item_id.is_not(None)
            )
        )
        if migrated_count:
            raise RuntimeError(
                "Legacy exercises have already been transformed. "
                "The command did not change any data."
            )

        await session.rollback()
        async with session.begin():
            course_version = await session.scalar(
                select(CourseVersionBD).where(
                    CourseVersionBD.code == course_version_code,
                    CourseVersionBD.is_active.is_(True),
                )
            )
            if course_version is None:
                raise RuntimeError("Course version disappeared during transformation")
            await _transform(session, course_version, plan, items_by_task)

        print("Exercise v2 transformation completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform confirmed legacy trainers into Exercise v2.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Write v2 data. Without this flag the command is a dry run.",
    )
    parser.add_argument(
        "--course-version",
        default="2026",
        help="Active course version containing the transformed theory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(transform(args.course_version, args.execute))


if __name__ == "__main__":
    main()
