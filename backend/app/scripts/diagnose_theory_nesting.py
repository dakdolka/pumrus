"""Print a read-only report about legacy and v2 theory block nesting."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.db import async_session_factory


REPORT_SQL = """
WITH mapped AS (
    SELECT
        child.id AS child_v2_id,
        child.document_version_id,
        child.parent_block_id AS actual_parent_v2_id,
        child.block_type AS child_type,
        legacy_child.id AS child_legacy_id,
        legacy_child.parent_id AS expected_parent_legacy_id,
        parent.id AS expected_parent_v2_id,
        parent.block_type AS parent_type
    FROM theory_block_v2 AS child
    JOIN theory_block AS legacy_child
      ON legacy_child.id = child.source_legacy_block_id
    LEFT JOIN theory_block_v2 AS parent
      ON parent.source_legacy_block_id = legacy_child.parent_id
     AND parent.document_version_id = child.document_version_id
)
SELECT
    COUNT(*) AS mapped_blocks,
    COUNT(*) FILTER (
        WHERE expected_parent_legacy_id IS NOT NULL
    ) AS legacy_nested_blocks,
    COUNT(*) FILTER (
        WHERE actual_parent_v2_id IS NOT NULL
    ) AS v2_nested_blocks,
    COUNT(*) FILTER (
        WHERE expected_parent_legacy_id IS NOT NULL
          AND expected_parent_v2_id IS NULL
    ) AS missing_v2_parents,
    COUNT(*) FILTER (
        WHERE expected_parent_v2_id IS NOT NULL
          AND actual_parent_v2_id IS DISTINCT FROM expected_parent_v2_id
    ) AS incorrect_v2_links
FROM mapped
"""


SAMPLES_SQL = """
SELECT
    child.id AS child_v2_id,
    child.block_type AS child_type,
    child.parent_block_id AS actual_parent_v2_id,
    legacy_child.id AS child_legacy_id,
    legacy_child.parent_id AS expected_parent_legacy_id,
    parent.id AS expected_parent_v2_id,
    parent.block_type AS expected_parent_type
FROM theory_block_v2 AS child
JOIN theory_block AS legacy_child
  ON legacy_child.id = child.source_legacy_block_id
LEFT JOIN theory_block_v2 AS parent
  ON parent.source_legacy_block_id = legacy_child.parent_id
 AND parent.document_version_id = child.document_version_id
WHERE legacy_child.parent_id IS NOT NULL
ORDER BY child.document_version_id, legacy_child.parent_id, child.sort_order
LIMIT 30
"""


async def main() -> None:
    async with async_session_factory() as session:
        report = (await session.execute(text(REPORT_SQL))).mappings().one()
        print("Theory nesting report:")
        for key, value in report.items():
            print(f"  {key}: {value}")

        print("Nested block samples:")
        samples = (await session.execute(text(SAMPLES_SQL))).mappings().all()
        if not samples:
            print("  no legacy nested blocks found")
        for sample in samples:
            print("  " + ", ".join(f"{key}={value}" for key, value in sample.items()))


if __name__ == "__main__":
    asyncio.run(main())
