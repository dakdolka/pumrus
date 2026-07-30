"""Import the bundled task 15 Н/НН dataset into Exercise v2.

The command is a dry run unless ``--execute`` is provided.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.api.v2.admin_router import _exercise_payload
from app.api.v2.exercise_import import parse_exercises
from app.core.db import async_session_factory
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseVersionBD,
)


DATASET = Path(__file__).with_name("txts") / "task15_nn.txt"
SET_TITLE = "Н и НН"


async def import_dataset(execute: bool) -> None:
    parsed = parse_exercises(DATASET.read_text(encoding="utf-8"), "single_choice")
    if parsed["errors"]:
        raise RuntimeError(f"Dataset parser errors: {parsed['errors'][:3]}")
    if len(parsed["rows"]) != 408:
        raise RuntimeError(f"Expected 408 rows, found {len(parsed['rows'])}")

    async with async_session_factory() as db:
        course_version = await db.scalar(
            select(CourseVersionBD).where(CourseVersionBD.is_active.is_(True))
        )
        if course_version is None:
            raise RuntimeError("Active course version not found")
        task = await db.scalar(
            select(ExamTaskBD).where(
                ExamTaskBD.course_version_id == course_version.id,
                ExamTaskBD.number == 15,
            )
        )
        if task is None:
            raise RuntimeError("Exam task 15 not found")

        exercise_set = await db.scalar(
            select(ExerciseSetBD).where(
                ExerciseSetBD.course_version_id == course_version.id,
                ExerciseSetBD.exam_task_id == task.id,
                ExerciseSetBD.topic_id.is_(None),
                ExerciseSetBD.title == SET_TITLE,
            )
        )
        existing_signatures: set[str] = set()
        if exercise_set is not None:
            existing_rows = (
                await db.execute(
                    select(
                        ExerciseVersionBD.prompt_data,
                        ExerciseVersionBD.answer_config,
                    )
                    .join(
                        ExerciseBD,
                        ExerciseBD.published_version_id == ExerciseVersionBD.id,
                    )
                    .join(
                        ExerciseSetItemBD,
                        ExerciseSetItemBD.exercise_id == ExerciseBD.id,
                    )
                    .where(ExerciseSetItemBD.exercise_set_id == exercise_set.id)
                )
            ).all()
            existing_signatures = {
                json.dumps([prompt, answer], ensure_ascii=False, sort_keys=True)
                for prompt, answer in existing_rows
            }

        prepared: list[dict] = []
        for row in parsed["rows"]:
            payload = _exercise_payload("single_choice", row)
            signature = json.dumps(
                [payload["prompt"], payload["answer"]],
                ensure_ascii=False,
                sort_keys=True,
            )
            if signature not in existing_signatures:
                existing_signatures.add(signature)
                prepared.append(payload)

        print("Task 15 dataset import plan:")
        print(f"  dataset rows: {len(parsed['rows'])}")
        print(f"  existing duplicates: {len(parsed['rows']) - len(prepared)}")
        print(f"  exercises to create: {len(prepared)}")
        print(
            f"  target set: "
            f"{exercise_set.id if exercise_set else 'new'} ({SET_TITLE!r})"
        )
        if not execute:
            print("Dry run completed. No records were written.")
            print("Run again with --execute to import this dataset.")
            return
        if not prepared:
            print("Dataset is already imported. Nothing to do.")
            return

        if exercise_set is None:
            exercise_set = ExerciseSetBD(
                course_version_id=course_version.id,
                exam_task_id=task.id,
                topic_id=None,
                title=SET_TITLE,
                selection_strategy="all_shuffled",
                configuration={"sessionSize": 50, "pageSize": 5},
                status="published",
            )
            db.add(exercise_set)
            await db.flush()

        last_order = await db.scalar(
            select(func.max(ExerciseSetItemBD.sort_order)).where(
                ExerciseSetItemBD.exercise_set_id == exercise_set.id
            )
        )
        next_order = (last_order if last_order is not None else -1) + 1
        now = datetime.now(timezone.utc)
        for payload in prepared:
            exercise = ExerciseBD(
                course_version_id=course_version.id,
                status="published",
                source="task15_dataset",
            )
            db.add(exercise)
            await db.flush()
            version = ExerciseVersionBD(
                exercise_id=exercise.id,
                version_number=1,
                status="published",
                interaction_type="single_choice",
                response_schema_version=1,
                prompt_data=payload["prompt"],
                interaction_config=payload["interaction"],
                answer_config=payload["answer"],
                checker_type=payload["checker"],
                checker_config=payload["checkerConfig"],
                feedback_data=payload["feedback"],
                published_at=now,
            )
            db.add(version)
            await db.flush()
            exercise.published_version_id = version.id
            db.add(
                ExerciseTaskLinkBD(
                    exercise_id=exercise.id,
                    exam_task_id=task.id,
                    is_primary=True,
                )
            )
            db.add(
                ExerciseSetItemBD(
                    exercise_set_id=exercise_set.id,
                    exercise_id=exercise.id,
                    sort_order=next_order,
                )
            )
            next_order += 1

        await db.commit()
        print(
            f"Imported {len(prepared)} exercises into task 15 set "
            f"{exercise_set.id} ({exercise_set.title!r})."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    asyncio.run(import_dataset(args.execute))


if __name__ == "__main__":
    main()
