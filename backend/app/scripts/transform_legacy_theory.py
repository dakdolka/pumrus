"""Transform imported legacy theory into the v2 catalog and document model."""

from __future__ import annotations

import argparse
import asyncio
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
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


GENERAL_THEORY_RE = re.compile(r"^\s*№?\s*\d+\s+общее\s*$", re.IGNORECASE)
TASK_NUMBER_RE = re.compile(r"^\s*(\d{1,2})(?:\s+|$)")

# These legacy records have no association row, but their subject is
# unambiguous and was confirmed as part of task 10.
CONFIRMED_THEORY_TASK_LINKS: dict[int, tuple[int, ...]] = {
    5: (10,),   # Неизменяемые приставки
    30: (10,),  # Другие приставки
}


def _task_number(name: str) -> int | None:
    match = TASK_NUMBER_RE.match(name or "")
    if not match:
        return None
    number = int(match.group(1))
    return number if 1 <= number <= 27 else None


def _task_title(number: int, legacy_names: list[str]) -> str:
    for name in legacy_names:
        suffix = TASK_NUMBER_RE.sub("", name, count=1).strip(" .-")
        if suffix:
            return suffix
    return f"Задание {number}"


def _convert_block(
    legacy_type: str | None,
    content: str,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    legacy_type = legacy_type or "text"
    content = (content or "").replace("\\n", "\n")
    settings: dict[str, Any] = {"legacyType": legacy_type}

    if legacy_type == "title":
        return "rich_text", {"markdown": content}, {**settings, "variant": "heading_1"}
    if legacy_type == "subtitle":
        return "rich_text", {"markdown": content}, {**settings, "variant": "heading_2"}
    if legacy_type == "text":
        return "rich_text", {"markdown": content}, settings
    if legacy_type in {"rule", "important", "note", "exception"}:
        variant = {
            "rule": "rule",
            "important": "important",
            "note": "note",
            "exception": "warning",
        }[legacy_type]
        return "callout", {"markdown": content, "variant": variant}, settings
    if legacy_type == "example":
        return "example", {"markdown": content}, settings
    if legacy_type == "svg":
        return (
            "image",
            {"sourceType": "inline_svg", "svg": content},
            settings,
        )
    if legacy_type == "group":
        return "section", {"title": content}, settings
    if legacy_type == "link":
        return "rich_text", {"markdown": content}, {**settings, "variant": "link"}
    return "rich_text", {"markdown": content}, settings


async def _load_legacy_theory(
    session: AsyncSession,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[int, int]],
    dict[int, list[str]],
]:
    theories = [
        dict(row)
        for row in (
            await session.execute(
                text('SELECT id, name FROM "theory" ORDER BY id')
            )
        ).mappings()
    ]
    task_theories = [
        dict(row)
        for row in (
            await session.execute(
                text('SELECT id, name FROM "task_theory" ORDER BY id')
            )
        ).mappings()
    ]
    associations = [
        dict(row)
        for row in (
            await session.execute(
                text(
                    """
                    SELECT theory_id, task_theory_id, "order"
                    FROM "task_theory2theory"
                    ORDER BY task_theory_id, "order", theory_id
                    """
                )
            )
        ).mappings()
    ]

    task_number_by_legacy_id: dict[int, int] = {}
    legacy_names_by_number: dict[int, list[str]] = defaultdict(list)
    for item in task_theories:
        number = _task_number(item["name"])
        if number is not None:
            task_number_by_legacy_id[item["id"]] = number
            legacy_names_by_number[number].append(item["name"])

    theory_task_orders: dict[int, dict[int, int]] = defaultdict(dict)
    for association in associations:
        number = task_number_by_legacy_id.get(association["task_theory_id"])
        if number is not None:
            current_order = theory_task_orders[association["theory_id"]].get(
                number
            )
            association_order = int(association["order"])
            if current_order is None or association_order < current_order:
                theory_task_orders[association["theory_id"]][number] = (
                    association_order
                )

    for theory_id, numbers in CONFIRMED_THEORY_TASK_LINKS.items():
        for number in numbers:
            theory_task_orders[theory_id].setdefault(number, 999)

    return theories, theory_task_orders, legacy_names_by_number


def _print_plan(
    theories: list[dict[str, Any]],
    theory_task_orders: dict[int, dict[int, int]],
) -> list[dict[str, Any]]:
    importable = []
    ignored_general = []
    unresolved = []

    for theory in theories:
        if GENERAL_THEORY_RE.match(theory["name"]):
            ignored_general.append(theory)
            continue
        if not theory_task_orders.get(theory["id"]):
            unresolved.append(theory)
            continue
        importable.append(theory)

    print("Theory v2 transformation plan:")
    print("  exam tasks to create: 27")
    print(f"  topic theories to migrate: {len(importable)}")
    print(f"  ignored 'Общее' documents: {len(ignored_general)}")
    print(f"  unresolved theories: {len(unresolved)}")

    for theory in importable:
        numbers = ", ".join(
            str(number)
            for number in sorted(theory_task_orders[theory["id"]])
        )
        print(f"  topic {theory['id']}: {theory['name']} -> task(s) {numbers}")

    for theory in ignored_general:
        print(f"  ignored {theory['id']}: {theory['name']}")

    for theory in unresolved:
        print(f"  unresolved {theory['id']}: {theory['name']}")

    if unresolved:
        raise RuntimeError(
            "Some theory records have no confirmed task association. "
            "Resolve them before executing the transformation."
        )

    return importable


async def _get_or_create_catalog(
    session: AsyncSession,
    version_code: str,
    legacy_names_by_number: dict[int, list[str]],
) -> tuple[CourseVersionBD, dict[int, ExamTaskBD]]:
    course = await session.scalar(
        select(CourseBD).where(CourseBD.code == "ege-russian")
    )
    if course is None:
        course = CourseBD(
            code="ege-russian",
            title="ЕГЭ по русскому языку",
            description="Подготовка к ЕГЭ по русскому языку",
            status="published",
        )
        session.add(course)
        await session.flush()

    course_version = await session.scalar(
        select(CourseVersionBD).where(
            CourseVersionBD.course_id == course.id,
            CourseVersionBD.code == version_code,
        )
    )
    if course_version is None:
        course_version = CourseVersionBD(
            course_id=course.id,
            code=version_code,
            title=f"ЕГЭ по русскому языку — {version_code}",
            status="published",
            is_active=True,
        )
        session.add(course_version)
        await session.flush()

    tasks: dict[int, ExamTaskBD] = {}
    for number in range(1, 28):
        task = await session.scalar(
            select(ExamTaskBD).where(
                ExamTaskBD.course_version_id == course_version.id,
                ExamTaskBD.number == number,
            )
        )
        if task is None:
            task = ExamTaskBD(
                course_version_id=course_version.id,
                code=f"task-{number}",
                number=number,
                title=_task_title(
                    number,
                    legacy_names_by_number.get(number, []),
                ),
                short_description=None,
                sort_order=number,
                status="published",
            )
            session.add(task)
            await session.flush()
        tasks[number] = task

    return course_version, tasks


async def _migrate_theory(
    session: AsyncSession,
    course_version: CourseVersionBD,
    tasks: dict[int, ExamTaskBD],
    theories: list[dict[str, Any]],
    theory_task_orders: dict[int, dict[int, int]],
) -> None:
    published_at = datetime.now(timezone.utc)

    for theory in theories:
        legacy_theory_id = theory["id"]
        existing = await session.scalar(
            select(TopicBD).where(
                TopicBD.source_legacy_theory_id == legacy_theory_id
            )
        )
        if existing is not None:
            print(f"Skipped existing topic for legacy theory {legacy_theory_id}")
            continue

        topic = TopicBD(
            course_version_id=course_version.id,
            code=f"legacy-theory-{legacy_theory_id}",
            title=theory["name"],
            short_description=None,
            status="published",
            source_legacy_theory_id=legacy_theory_id,
        )
        session.add(topic)
        await session.flush()

        ordered_task_links = sorted(
            theory_task_orders[legacy_theory_id].items(),
            key=lambda item: (item[1], item[0]),
        )
        for link_index, (task_number, sort_order) in enumerate(
            ordered_task_links,
            start=1,
        ):
            session.add(
                ExamTaskTopicBD(
                    exam_task_id=tasks[task_number].id,
                    topic_id=topic.id,
                    sort_order=sort_order,
                    is_primary=link_index == 1,
                )
            )

        document = TheoryDocumentBD(
            topic_id=topic.id,
            title=theory["name"],
            status="published",
        )
        session.add(document)
        await session.flush()

        version = TheoryDocumentVersionBD(
            document_id=document.id,
            version_number=1,
            status="published",
            source_legacy_theory_id=legacy_theory_id,
            published_at=published_at,
        )
        session.add(version)
        await session.flush()

        legacy_blocks = [
            dict(row)
            for row in (
                await session.execute(
                    text(
                        """
                        SELECT id, type, content, parent_id, "order"
                        FROM "theory_block"
                        WHERE theory_id = :theory_id
                        ORDER BY id
                        """
                    ),
                    {"theory_id": legacy_theory_id},
                )
            ).mappings()
        ]

        block_by_legacy_id: dict[int, TheoryBlockV2BD] = {}
        for legacy_block in legacy_blocks:
            block_type, data, block_settings = _convert_block(
                legacy_block["type"],
                legacy_block["content"],
            )
            block = TheoryBlockV2BD(
                document_version_id=version.id,
                block_type=block_type,
                schema_version=1,
                data=data,
                settings=block_settings,
                sort_order=legacy_block["order"],
                source_legacy_block_id=legacy_block["id"],
            )
            session.add(block)
            await session.flush()
            block_by_legacy_id[legacy_block["id"]] = block

        for legacy_block in legacy_blocks:
            parent_id = legacy_block["parent_id"]
            if parent_id is not None and parent_id in block_by_legacy_id:
                block_by_legacy_id[legacy_block["id"]].parent_block_id = (
                    block_by_legacy_id[parent_id].id
                )

        document.published_version_id = version.id
        print(
            f"Migrated theory {legacy_theory_id}: {theory['name']} "
            f"({len(legacy_blocks)} blocks)"
        )


async def transform(version_code: str, execute: bool) -> None:
    async with async_session_factory() as session:
        theories, theory_task_orders, legacy_names = await _load_legacy_theory(
            session
        )
        importable = _print_plan(theories, theory_task_orders)

        if not execute:
            print("Dry run completed. No v2 records were written.")
            print("Run again with --execute to transform this theory.")
            return

        migrated_count = await session.scalar(
            select(func.count(TheoryDocumentVersionBD.id)).where(
                TheoryDocumentVersionBD.source_legacy_theory_id.is_not(None)
            )
        )
        if migrated_count:
            raise RuntimeError(
                "Legacy theory has already been transformed. "
                "The command did not change any data."
            )

        await session.rollback()
        async with session.begin():
            course_version, tasks = await _get_or_create_catalog(
                session,
                version_code,
                legacy_names,
            )
            await _migrate_theory(
                session,
                course_version,
                tasks,
                importable,
                theory_task_orders,
            )

        print("Theory v2 transformation completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform imported legacy theory into the v2 model."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Write v2 data. Without this flag the command is a dry run.",
    )
    parser.add_argument(
        "--course-version",
        default="2026",
        help="Course version code to create or reuse.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(transform(args.course_version, args.execute))


if __name__ == "__main__":
    main()
