"""Preview or add homonymy to task 9, preserving the current content and history.

Offline: python -m app.scripts.add_task9_homonymy --preview-json preview.json
Database: python -m app.scripts.add_task9_homonymy --course-version CODE
Write a draft: add --execute. Publish that new version: add --execute --publish.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.task9_homonymy import MARKER, REVISION, TOPIC_CODE, plan_patch


def baseline_blocks() -> list[dict[str, Any]]:
    from app.scripts.curated_orthography import TASK9

    topic = next(t for t in TASK9["topics"] if t["code"] == TOPIC_CODE)
    return [
        {**deepcopy(b), "id": i + 1, "parent_id": None, "sort_order": i, "schema_version": 1}
        for i, b in enumerate(topic["blocks"])
    ]


def db_record(block: Any) -> dict[str, Any]:
    return {
        "id": block.id, "parent_id": block.parent_block_id, "type": block.block_type,
        "schema_version": block.schema_version, "data": deepcopy(block.data),
        "settings": deepcopy(block.settings or {}), "sort_order": block.sort_order,
    }


async def run(course_version: str, execute: bool, publish: bool) -> None:
    # Keep offline preview usable without database settings or dependencies.
    from sqlalchemy import func, select
    from app.core.db import async_session_factory
    from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, ExamTaskTopicBD, TopicBD
    from app.infra.content.models import TheoryBlockV2BD, TheoryDocumentBD, TheoryDocumentVersionBD

    async with async_session_factory() as session:
        async with session.begin():
            statement = (
                select(TheoryDocumentBD)
                .join(TopicBD, TheoryDocumentBD.topic_id == TopicBD.id)
                .join(ExamTaskTopicBD, ExamTaskTopicBD.topic_id == TopicBD.id)
                .join(ExamTaskBD, ExamTaskBD.id == ExamTaskTopicBD.exam_task_id)
                .join(CourseVersionBD, CourseVersionBD.id == ExamTaskBD.course_version_id)
                .where(
                    CourseVersionBD.code == course_version, ExamTaskBD.number == 9,
                    TopicBD.course_version_id == CourseVersionBD.id,
                    TopicBD.code == TOPIC_CODE,
                    TopicBD.status.in_(["published", "published_manual"]),
                )
            )
            if execute:
                statement = statement.with_for_update(of=TheoryDocumentBD)
            documents = list((await session.scalars(statement)).all())
            if len(documents) != 1:
                raise ValueError(f"Expected one active task 9 alternation document; found {len(documents)}")
            document = documents[0]
            if document.published_version_id is None:
                raise ValueError("The document has no published version to extend")
            drafts = list((await session.scalars(select(TheoryDocumentVersionBD).where(
                TheoryDocumentVersionBD.document_id == document.id,
                TheoryDocumentVersionBD.status == "draft",
            ))).all())
            if drafts:
                draft_ids = ", ".join(str(d.id) for d in drafts)
                raise ValueError(f"Existing draft(s): {draft_ids}. Review them in the editor first; no changes made")

            source = list((await session.scalars(select(TheoryBlockV2BD).where(
                TheoryBlockV2BD.document_version_id == document.published_version_id,
            ).order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id))).all())
            records, changes = plan_patch([db_record(b) for b in source])
            print(f"Document: {document.id}; published version: {document.published_version_id}")
            if not changes:
                print("Homonymy is already present; no changes needed.")
                return
            for change in changes:
                print(f"  + {change}")
            print(f"Preserved blocks: {len(source)}; added blocks: {len(records) - len(source)}")
            if not execute:
                print("Dry run: no records written. Use --execute to create a draft.")
                return

            latest = await session.scalar(select(func.max(TheoryDocumentVersionBD.version_number)).where(
                TheoryDocumentVersionBD.document_id == document.id,
            ))
            version = TheoryDocumentVersionBD(
                document_id=document.id, version_number=(latest or 0) + 1,
                status="published" if publish else "draft",
                published_at=datetime.now(timezone.utc) if publish else None,
            )
            session.add(version)
            await session.flush()
            clones = {}
            for record in records:
                clone = TheoryBlockV2BD(
                    document_version_id=version.id, block_type=record["type"],
                    schema_version=record["schema_version"], data=deepcopy(record["data"]),
                    settings=deepcopy(record["settings"]), sort_order=record["sort_order"],
                )
                session.add(clone)
                clones[record["id"]] = clone
            await session.flush()
            for record in records:
                parent_id = record.get("parent_id")
                if parent_id is not None:
                    if parent_id not in clones:
                        raise ValueError(f"Missing parent {parent_id!r}; transaction will be rolled back")
                    clones[record["id"]].parent_block_id = clones[parent_id].id
            previous = document.published_version_id
            if publish:
                document.published_version_id = version.id
            await session.flush()
            version_id = version.id
        print(f"Committed {version.status} version {version_id}; previous published version: {previous}")
        if not publish:
            print("Open task 9 → Чередующиеся корни → Теория → Редактор to review and publish the draft.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-version", help="Explicit course version code")
    parser.add_argument("--preview-json", type=Path, help="Offline before/after content preview; does not connect to a database")
    parser.add_argument("--execute", action="store_true", help="Save as a new draft")
    parser.add_argument("--publish", action="store_true", help="Publish the newly created version (requires --execute)")
    args = parser.parse_args()
    if args.publish and not args.execute:
        parser.error("--publish requires --execute")
    if args.preview_json:
        if args.execute or args.publish:
            parser.error("--preview-json cannot be combined with database writes")
        before = baseline_blocks()
        after, changes = plan_patch(before)
        args.preview_json.write_text(json.dumps({
            "revision": REVISION, "marker": MARKER, "origin": "repository baseline; live database was not read",
            "changes": changes, "before": before, "after": after,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Offline preview saved: {args.preview_json}")
        return
    if not args.course_version:
        parser.error("Pass --course-version CODE for database operations, or --preview-json PATH")
    asyncio.run(run(args.course_version, args.execute, args.publish))


if __name__ == "__main__":
    main()
