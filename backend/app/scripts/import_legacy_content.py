"""Import legacy learning content from MySQL into PostgreSQL.

Alembic owns the target schema. This script only copies content records and
deliberately skips users, sessions, and mistakes.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import settings


@dataclass(frozen=True)
class TableSpec:
    name: str
    columns: tuple[str, ...]
    boolean_columns: frozenset[str] = field(default_factory=frozenset)
    has_sequence: bool = False


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        "option",
        ("id", "content", "extras", "created_at", "updated_at"),
        has_sequence=True,
    ),
    TableSpec(
        "option_set",
        ("id", "name", "created_at", "updated_at"),
        has_sequence=True,
    ),
    TableSpec(
        "task_group",
        ("id", "name", "created_at", "updated_at"),
        has_sequence=True,
    ),
    TableSpec(
        "theory_type",
        ("id", "name"),
        has_sequence=True,
    ),
    TableSpec(
        "theory",
        ("id", "name", "created_at", "updated_at"),
        has_sequence=True,
    ),
    TableSpec(
        "task_theory_group",
        ("id", "name", "is_single", "created_at", "updated_at"),
        boolean_columns=frozenset({"is_single"}),
        has_sequence=True,
    ),
    TableSpec(
        "option_set2option",
        ("option_set_id", "option_id"),
    ),
    TableSpec(
        "task",
        (
            "id",
            "name",
            "task_group_fk",
            "default_option_set_fk",
            "trainer_type",
            "created_at",
            "updated_at",
        ),
        has_sequence=True,
    ),
    TableSpec(
        "task_item",
        (
            "id",
            "content_raw",
            "content_visible",
            "content_correct",
            "correct_option_fk",
            "option_set_override_fk",
            "notice_wrong",
            "notice_right",
            "task_id",
            "created_at",
            "updated_at",
        ),
        has_sequence=True,
    ),
    TableSpec(
        "theory2theory_type",
        ("theory_id", "type_id"),
    ),
    TableSpec(
        "theory_block",
        (
            "id",
            "content",
            "type",
            "theory_id",
            "parent_id",
            "order",
            "created_at",
            "updated_at",
        ),
        has_sequence=True,
    ),
    TableSpec(
        "task_theory",
        ("id", "name", "group_id", "created_at", "updated_at"),
        has_sequence=True,
    ),
    TableSpec(
        "task_theory2theory",
        (
            "theory_id",
            "task_theory_id",
            "order",
            "created_at",
            "updated_at",
        ),
    ),
)


def _validate_urls(source_url: URL, target_url: URL) -> None:
    if not source_url.drivername.startswith("mysql"):
        raise ValueError("LEGACY_DATABASE_URL must point to MySQL")
    if not target_url.drivername.startswith("postgresql"):
        raise ValueError("DATABASE_URL must point to PostgreSQL")
    if source_url.render_as_string(hide_password=False) == target_url.render_as_string(
        hide_password=False
    ):
        raise ValueError("Source and target databases must be different")


def _source_select(spec: TableSpec) -> str:
    columns = ", ".join(f"`{column}`" for column in spec.columns)
    return f"SELECT {columns} FROM `{spec.name}` ORDER BY 1"


def _target_insert(spec: TableSpec) -> str:
    columns = ", ".join(f'"{column}"' for column in spec.columns)
    values = ", ".join(f":{column}" for column in spec.columns)
    return f'INSERT INTO "{spec.name}" ({columns}) VALUES ({values})'


def _normalize_row(spec: TableSpec, row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    for column in spec.boolean_columns:
        value = normalized.get(column)
        if value is not None:
            normalized[column] = bool(value)
    return normalized


async def _count(connection: AsyncConnection, table_name: str, mysql: bool) -> int:
    quote = "`" if mysql else '"'
    result = await connection.execute(
        text(f"SELECT COUNT(*) FROM {quote}{table_name}{quote}")
    )
    return int(result.scalar_one())


async def _assert_target_is_empty(connection: AsyncConnection) -> None:
    occupied = []
    for spec in TABLES:
        count = await _count(connection, spec.name, mysql=False)
        if count:
            occupied.append(f"{spec.name}={count}")

    if occupied:
        details = ", ".join(occupied)
        raise RuntimeError(
            "Target content tables are not empty. "
            f"Import was cancelled: {details}"
        )


async def _load_source_rows(
    connection: AsyncConnection,
    spec: TableSpec,
) -> list[dict[str, Any]]:
    result = await connection.execute(text(_source_select(spec)))
    return [
        _normalize_row(spec, dict(row))
        for row in result.mappings().all()
    ]


async def _reset_sequence(connection: AsyncConnection, table_name: str) -> None:
    await connection.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('"{table_name}"', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM "{table_name}"
            """
        )
    )


async def _print_source_summary(source: AsyncConnection) -> None:
    print("Legacy content summary:")
    total = 0
    for spec in TABLES:
        count = await _count(source, spec.name, mysql=True)
        total += count
        print(f"  {spec.name}: {count}")
    print(f"  total: {total}")


async def import_content(source_dsn: str, execute: bool) -> None:
    source_url = make_url(source_dsn)
    target_url = make_url(settings.database_url)
    _validate_urls(source_url, target_url)

    source_engine = create_async_engine(source_url, pool_pre_ping=True)
    target_engine = create_async_engine(target_url, pool_pre_ping=True)

    try:
        async with source_engine.connect() as source:
            await _print_source_summary(source)

            async with target_engine.connect() as target:
                await _assert_target_is_empty(target)

            if not execute:
                print("Dry run completed. No data was written.")
                print("Run again with --execute to import this content.")
                return

            async with target_engine.begin() as target:
                for spec in TABLES:
                    rows = await _load_source_rows(source, spec)
                    if rows:
                        await target.execute(text(_target_insert(spec)), rows)

                    target_count = await _count(target, spec.name, mysql=False)
                    if target_count != len(rows):
                        raise RuntimeError(
                            f"Count mismatch for {spec.name}: "
                            f"source={len(rows)}, target={target_count}"
                        )

                    if spec.has_sequence:
                        await _reset_sequence(target, spec.name)

                    print(f"Imported {spec.name}: {target_count}")

            print("Legacy content import completed successfully.")
    finally:
        await source_engine.dispose()
        await target_engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy legacy learning content from MySQL to PostgreSQL."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Write data. Without this flag the command performs a dry run.",
    )
    parser.add_argument(
        "--source-url",
        default=os.getenv("LEGACY_DATABASE_URL"),
        help="MySQL async SQLAlchemy URL; defaults to LEGACY_DATABASE_URL.",
    )
    args = parser.parse_args()
    if not args.source_url:
        parser.error(
            "Provide --source-url or set LEGACY_DATABASE_URL"
        )
    return args


def main() -> None:
    args = parse_args()
    asyncio.run(import_content(args.source_url, execute=args.execute))


if __name__ == "__main__":
    main()
