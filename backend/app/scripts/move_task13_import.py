"""Move an accidentally imported task 13 batch to the correct exercise set.

The command is deliberately conservative. By default it only prints a plan.
It recognises task 13 rows by all of these properties:

* exercise source is ``form_bulk_import``;
* the prompt contains exactly one ``(НЕ)`` or ``(НИ)`` marker;
* the interaction offers exactly ``слитно`` and ``раздельно``;
* the exercise is not already linked to exam task 13.
"""

from __future__ import annotations

import argparse
import asyncio
import re
from collections import Counter

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.infra.catalog.models import ExamTaskBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
)


MARKER_RE = re.compile(r"\((?:НЕ|НИ)\)", re.IGNORECASE)
EXPECTED_OPTIONS = {"слитно", "раздельно"}


def _is_task13_row(
    prompt_data: dict,
    interaction_config: dict,
) -> bool:
    prompt = str((prompt_data or {}).get("content", ""))
    labels = {
        str(option.get("label", "")).strip().casefold()
        for option in (interaction_config or {}).get("options", [])
        if isinstance(option, dict)
    }
    return len(MARKER_RE.findall(prompt)) == 1 and labels == EXPECTED_OPTIONS


async def _find_candidates(
    db: AsyncSession,
) -> list[tuple[ExerciseBD, ExerciseVersionBD, int, str, int]]:
    rows = (
        await db.execute(
            select(
                ExerciseBD,
                ExerciseVersionBD,
                ExerciseSetBD.id,
                ExerciseSetBD.title,
                ExamTaskBD.number,
            )
            .join(
                ExerciseVersionBD,
                ExerciseVersionBD.id == ExerciseBD.published_version_id,
            )
            .join(
                ExerciseSetItemBD,
                ExerciseSetItemBD.exercise_id == ExerciseBD.id,
            )
            .join(
                ExerciseSetBD,
                ExerciseSetBD.id == ExerciseSetItemBD.exercise_set_id,
            )
            .join(ExamTaskBD, ExamTaskBD.id == ExerciseSetBD.exam_task_id)
            .where(ExerciseBD.source == "form_bulk_import")
        )
    ).all()
    return [
        row
        for row in rows
        if row[4] != 13 and _is_task13_row(row[1].prompt_data, row[1].interaction_config)
    ]


async def _resolve_target(
    db: AsyncSession,
    course_version_id: int,
    requested_set_id: int | None,
    execute: bool,
) -> tuple[ExamTaskBD, ExerciseSetBD | None]:
    task = await db.scalar(
        select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == course_version_id,
            ExamTaskBD.number == 13,
        )
    )
    if task is None:
        raise RuntimeError("Exam task 13 does not exist in the candidate course version.")

    if requested_set_id is not None:
        target = await db.get(ExerciseSetBD, requested_set_id)
        if (
            target is None
            or target.course_version_id != course_version_id
            or target.exam_task_id != task.id
        ):
            raise RuntimeError("--target-set-id must point to an exercise set for task 13.")
        return task, target

    targets = list(
        (
            await db.scalars(
                select(ExerciseSetBD).where(
                    ExerciseSetBD.course_version_id == course_version_id,
                    ExerciseSetBD.exam_task_id == task.id,
                    ExerciseSetBD.topic_id.is_(None),
                )
            )
        ).all()
    )
    if len(targets) > 1:
        details = ", ".join(f"{item.id}: {item.title}" for item in targets)
        raise RuntimeError(
            "Several task 13 sets exist; repeat with --target-set-id. "
            f"Candidates: {details}"
        )
    if targets:
        return task, targets[0]
    if not execute:
        return task, None

    target = ExerciseSetBD(
        course_version_id=course_version_id,
        exam_task_id=task.id,
        topic_id=None,
        title="НЕ с разными частями речи",
        selection_strategy="all_shuffled",
        configuration={"sessionSize": 50, "pageSize": 5},
        status="published",
    )
    db.add(target)
    await db.flush()
    return task, target


async def move(
    execute: bool,
    expected_count: int,
    target_set_id: int | None,
) -> None:
    async with async_session_factory() as db:
        candidates = await _find_candidates(db)
        unique_exercises = {exercise.id: exercise for exercise, *_ in candidates}
        source_sets = Counter(
            (set_id, set_title, task_number)
            for _, _, set_id, set_title, task_number in candidates
        )
        course_versions = {exercise.course_version_id for exercise in unique_exercises.values()}

        print("Task 13 accidental import recovery plan:")
        print(f"  matched exercises: {len(unique_exercises)}")
        for (set_id, title, task_number), count in source_sets.items():
            print(f"  source set {set_id}: task {task_number}, {title!r} -> {count}")

        if not unique_exercises:
            print("No misplaced task 13 exercises found. Nothing to do.")
            return
        if len(course_versions) != 1:
            raise RuntimeError(
                f"Candidates span several course versions: {sorted(course_versions)}"
            )
        if len(unique_exercises) != expected_count:
            raise RuntimeError(
                f"Expected {expected_count} exercises, found {len(unique_exercises)}. "
                "Nothing was changed. Verify the count before overriding --expected-count."
            )

        course_version_id = next(iter(course_versions))
        task, target = await _resolve_target(
            db,
            course_version_id,
            target_set_id,
            execute,
        )
        if target is None:
            print("  target: a new task 13 set 'НЕ с разными частями речи'")
        else:
            print(f"  target set {target.id}: task 13, {target.title!r}")

        if not execute:
            print("Dry run completed. No records were changed.")
            print("Run again with --execute after checking this plan.")
            return

        assert target is not None
        exercise_ids = list(unique_exercises)
        await db.execute(
            delete(ExerciseSetItemBD).where(
                ExerciseSetItemBD.exercise_id.in_(exercise_ids)
            )
        )
        await db.execute(
            delete(ExerciseTaskLinkBD).where(
                ExerciseTaskLinkBD.exercise_id.in_(exercise_ids)
            )
        )
        await db.execute(
            delete(ExerciseTopicLinkBD).where(
                ExerciseTopicLinkBD.exercise_id.in_(exercise_ids)
            )
        )

        last_order = await db.scalar(
            select(func.max(ExerciseSetItemBD.sort_order)).where(
                ExerciseSetItemBD.exercise_set_id == target.id
            )
        )
        next_order = (last_order if last_order is not None else -1) + 1
        for exercise_id in sorted(exercise_ids):
            db.add(
                ExerciseSetItemBD(
                    exercise_set_id=target.id,
                    exercise_id=exercise_id,
                    sort_order=next_order,
                )
            )
            db.add(
                ExerciseTaskLinkBD(
                    exercise_id=exercise_id,
                    exam_task_id=task.id,
                    is_primary=True,
                )
            )
            unique_exercises[exercise_id].source = "form_bulk_import:task13"
            next_order += 1

        await db.commit()
        print(
            f"Moved {len(exercise_ids)} exercises to task 13 set "
            f"{target.id} ({target.title!r})."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply the move. Without this flag the command is read-only.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=420,
        help="Safety check for the number of matched exercises (default: 420).",
    )
    parser.add_argument(
        "--target-set-id",
        type=int,
        help="Use a specific existing task 13 exercise set.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(move(args.execute, args.expected_count, args.target_set_id))


if __name__ == "__main__":
    main()
