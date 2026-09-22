"""Remove obsolete topics and their duplicate practice sets, preserving exercises.

Dry run by default. Before --execute, take and verify a PostgreSQL backup.
The transaction aborts if the live database differs from the reviewed inventory.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import delete, func, select, text, update

from app.core.db import async_session_factory
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, TopicBD
from app.infra.content.models import TheoryBlockV2BD, TheoryDocumentBD
from app.infra.exercises.models import (
    ExerciseBD, ExerciseSetBD, ExerciseSetItemBD, ExerciseTaskLinkBD, ExerciseTopicLinkBD,
    ExerciseVersionBD,
)
from app.infra.monetization.models import AccessPolicyResourceBD
from app.infra.practice.models import PracticeSessionBD, PracticeSessionItemBD


VISIBLE = frozenset({"published", "published_manual"})
STALE = frozenset({"deleted", "deprecated"})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def cleanup(execute: bool, backup_confirmed: bool) -> None:
    async with async_session_factory() as db:
        # All checks and writes see one serializable snapshot. A concurrent edit
        # either precedes our checks or makes the commit fail, never slips through.
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        course = await db.scalar(select(CourseVersionBD).where(CourseVersionBD.is_active.is_(True)))
        require(course is not None, "No active course version")
        tasks = list((await db.scalars(select(ExamTaskBD).where(
            ExamTaskBD.course_version_id == course.id
        ))).all())
        task_ids = {task.id for task in tasks}
        all_topics = list((await db.scalars(select(TopicBD).where(
            TopicBD.course_version_id == course.id
        ))).all())
        unexpected = [topic for topic in all_topics if topic.status not in VISIBLE | STALE]
        require(not unexpected, f"Unreviewed topic statuses: {[(t.id, t.status) for t in unexpected]}")
        stale = [topic for topic in all_topics if topic.status in STALE]
        stale_ids = {topic.id for topic in stale}
        require(len(stale) == 190, f"Expected 190 stale topics; found {len(stale)}. Re-audit first")

        stale_sets = list((await db.scalars(select(ExerciseSetBD).where(
            ExerciseSetBD.course_version_id == course.id,
            ExerciseSetBD.topic_id.in_(stale_ids),
        ))).all())
        require(len(stale_sets) == 29, f"Expected 29 obsolete sets; found {len(stale_sets)}. Re-audit first")
        set_ids = {item.id for item in stale_sets}
        require(all(item.status == "published" for item in stale_sets), "Unexpected set status")

        policies = list((await db.scalars(select(AccessPolicyResourceBD).where(
            ((AccessPolicyResourceBD.resource_type == "topic")
             & AccessPolicyResourceBD.resource_id.in_(stale_ids))
            | ((AccessPolicyResourceBD.resource_type == "exercise_set")
               & AccessPolicyResourceBD.resource_id.in_(set_ids))
        ))).all())
        require(not policies, f"Access policies still refer to obsolete content: {[p.id for p in policies]}")

        # A visible published document may not link to a set about to be removed.
        visible_topic_ids = {topic.id for topic in all_topics if topic.status in VISIBLE}
        visible_docs = list((await db.scalars(select(TheoryDocumentBD).where(
            (TheoryDocumentBD.exam_task_id.in_(task_ids))
            | TheoryDocumentBD.topic_id.in_(visible_topic_ids)
        ))).all())
        version_ids = {doc.published_version_id for doc in visible_docs if doc.published_version_id}
        blocks = list((await db.scalars(select(TheoryBlockV2BD).where(
            TheoryBlockV2BD.document_version_id.in_(version_ids),
            TheoryBlockV2BD.block_type == "practice_link",
        ))).all())
        obsolete_set_keys = {str(item_id) for item_id in set_ids}
        dangling = [block.id for block in blocks
                    if str((block.data or {}).get("exerciseSetId")) in obsolete_set_keys]
        require(not dangling, f"Visible theory links to obsolete sets in blocks: {dangling}")

        task_sets = list((await db.scalars(select(ExerciseSetBD).where(
            ExerciseSetBD.course_version_id == course.id,
            ExerciseSetBD.exam_task_id.in_(task_ids),
            ExerciseSetBD.topic_id.is_(None),
            ExerciseSetBD.status == "published",
        ))).all())
        by_task: dict[int, list[ExerciseSetBD]] = {}
        for item in task_sets:
            by_task.setdefault(item.exam_task_id, []).append(item)
        required_set_ids = set_ids | {item.id for item in task_sets}
        set_items = list((await db.scalars(select(ExerciseSetItemBD).where(
            ExerciseSetItemBD.exercise_set_id.in_(required_set_ids)
        ))).all())
        exercises_by_set: dict[int, set[int]] = {}
        for item in set_items:
            exercises_by_set.setdefault(item.exercise_set_id, set()).add(item.exercise_id)

        replacements: dict[int, int] = {}
        for old in stale_sets:
            candidates = by_task.get(old.exam_task_id, [])
            require(len(candidates) == 1,
                    f"Set {old.id}: expected exactly one published task-level set, found {len(candidates)}")
            target = candidates[0]
            missing = exercises_by_set.get(old.id, set()) - exercises_by_set.get(target.id, set())
            require(not missing, f"Set {old.id}: {len(missing)} exercises absent from task set {target.id}")
            require(old.access_level == target.access_level,
                    f"Set {old.id}: access level differs from task set {target.id}")
            replacements[old.id] = target.id

        topic_links = list((await db.scalars(select(ExerciseTopicLinkBD).where(
            ExerciseTopicLinkBD.topic_id.in_(stale_ids)
        ))).all())
        linked_exercise_ids = {link.exercise_id for link in topic_links}
        task_links = list((await db.scalars(select(ExerciseTaskLinkBD).where(
            ExerciseTaskLinkBD.exercise_id.in_(linked_exercise_ids),
            ExerciseTaskLinkBD.exam_task_id.in_(task_ids),
        ))).all())
        task_linked_ids = {link.exercise_id for link in task_links}
        require(linked_exercise_ids <= task_linked_ids,
                f"Exercises without task link: {sorted(linked_exercise_ids - task_linked_ids)[:20]}")

        sessions = list((await db.scalars(select(PracticeSessionBD).where(
            PracticeSessionBD.exercise_set_id.in_(set_ids)
        ))).all())
        if sessions:
            session_set = {session.id: session.exercise_set_id for session in sessions}
            session_exercises = list((await db.execute(select(
                PracticeSessionItemBD.session_id, ExerciseVersionBD.exercise_id
            ).join(ExerciseVersionBD,
                   ExerciseVersionBD.id == PracticeSessionItemBD.exercise_version_id)
             .where(PracticeSessionItemBD.session_id.in_(session_set)))).all())
            invalid_sessions = [session_id for session_id, exercise_id in session_exercises
                                if exercise_id not in exercises_by_set.get(
                                    replacements[session_set[session_id]], set())]
            require(not invalid_sessions,
                    f"Sessions contain exercises absent from replacement set: {sorted(set(invalid_sessions))}")
        print(f"Course: {course.code}; stale topics: {len(stale)}; duplicate sets: {len(stale_sets)}")
        print(f"Exercise-topic links to remove: {len(topic_links)}; exercises preserved: {len(linked_exercise_ids)}")
        print(f"Sessions to reattach to task-level sets: {len(sessions)}")
        for old in sorted(stale_sets, key=lambda item: item.id):
            print(f"  set {old.id} -> {replacements[old.id]} "
                  f"({len(exercises_by_set.get(old.id, set()))} exercises, all duplicated)")
        if not execute:
            print("DRY RUN: database unchanged. Take and verify a PostgreSQL backup before --execute.")
            return
        require(backup_confirmed, "--execute requires --backup-confirmed after verifying a PostgreSQL backup")

        # Keep attempt history and session items. Only the catalog context of
        # old sessions changes to the corresponding full-task set.
        for old_id, target_id in replacements.items():
            await db.execute(update(PracticeSessionBD).where(
                PracticeSessionBD.exercise_set_id == old_id
            ).values(exercise_set_id=target_id))
        old_docs = list((await db.scalars(select(TheoryDocumentBD).where(
            TheoryDocumentBD.topic_id.in_(stale_ids)
        ))).all())
        for doc in old_docs:
            doc.published_version_id = None  # break document/version FK cycle
        await db.flush()
        await db.execute(delete(ExerciseSetBD).where(ExerciseSetBD.id.in_(set_ids)))
        await db.execute(delete(TopicBD).where(TopicBD.id.in_(stale_ids)))
        remaining_topics = await db.scalar(select(func.count()).select_from(TopicBD).where(
            TopicBD.id.in_(stale_ids)))
        remaining_sets = await db.scalar(select(func.count()).select_from(ExerciseSetBD).where(
            ExerciseSetBD.id.in_(set_ids)))
        remaining_links = await db.scalar(select(func.count()).select_from(ExerciseTopicLinkBD).where(
            ExerciseTopicLinkBD.topic_id.in_(stale_ids)))
        remaining_exercises = await db.scalar(select(func.count()).select_from(ExerciseBD).where(
            ExerciseBD.id.in_(linked_exercise_ids)))
        remaining_sessions = await db.scalar(select(func.count()).select_from(PracticeSessionBD).where(
            PracticeSessionBD.id.in_({session.id for session in sessions})))
        require(not any((remaining_topics, remaining_sets, remaining_links)),
                "Post-cleanup validation failed: obsolete rows remain")
        require(remaining_exercises == len(linked_exercise_ids),
                "Post-cleanup validation failed: exercises were lost")
        require(remaining_sessions == len(sessions),
                "Post-cleanup validation failed: sessions were lost")
        await db.commit()
        print("DONE: 190 stale topics and 29 duplicate sets removed; exercises and attempts preserved.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Apply the reviewed cleanup")
    parser.add_argument("--backup-confirmed", action="store_true",
                        help="Confirm a current PostgreSQL backup was taken and verified")
    args = parser.parse_args()
    if args.backup_confirmed and not args.execute:
        parser.error("--backup-confirmed is meaningful only with --execute")
    asyncio.run(cleanup(args.execute, args.backup_confirmed))


if __name__ == "__main__":
    main()
