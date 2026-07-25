"""Restore nested theory blocks omitted by the original v2 transformer.

Revision ID: 20260725_0006
Revises: 20260725_0005
Create Date: 2026-07-25
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260725_0006"
down_revision: Union[str, Sequence[str], None] = "20260725_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        r"""
        WITH RECURSIVE legacy_tree AS (
            SELECT
                root.id,
                root.type::text AS legacy_type,
                root.content,
                root.parent_id,
                root."order",
                root.id AS root_id
            FROM theory_block AS root
            WHERE root.theory_id IS NOT NULL

            UNION ALL

            SELECT
                child.id,
                child.type::text,
                child.content,
                child.parent_id,
                child."order",
                parent.root_id
            FROM theory_block AS child
            JOIN legacy_tree AS parent ON child.parent_id = parent.id
        ),
        missing AS (
            SELECT
                tree.*,
                root_v2.document_version_id
            FROM legacy_tree AS tree
            JOIN theory_block_v2 AS root_v2
              ON root_v2.source_legacy_block_id = tree.root_id
            LEFT JOIN theory_block_v2 AS existing
              ON existing.source_legacy_block_id = tree.id
            WHERE tree.parent_id IS NOT NULL
              AND existing.id IS NULL
        )
        INSERT INTO theory_block_v2 (
            document_version_id,
            parent_block_id,
            block_type,
            schema_version,
            data,
            settings,
            sort_order,
            source_legacy_block_id,
            created_at,
            updated_at
        )
        SELECT
            document_version_id,
            NULL,
            CASE legacy_type
                WHEN 'group' THEN 'section'
                WHEN 'rule' THEN 'callout'
                WHEN 'important' THEN 'callout'
                WHEN 'note' THEN 'callout'
                WHEN 'exception' THEN 'callout'
                WHEN 'example' THEN 'example'
                WHEN 'svg' THEN 'image'
                ELSE 'rich_text'
            END,
            1,
            CASE legacy_type
                WHEN 'group' THEN jsonb_build_object(
                    'title', replace(COALESCE(content, ''), E'\\n', E'\n')
                )
                WHEN 'svg' THEN jsonb_build_object(
                    'sourceType', 'inline_svg',
                    'svg', COALESCE(content, '')
                )
                WHEN 'rule' THEN jsonb_build_object(
                    'markdown', replace(COALESCE(content, ''), E'\\n', E'\n'),
                    'variant', 'rule'
                )
                WHEN 'important' THEN jsonb_build_object(
                    'markdown', replace(COALESCE(content, ''), E'\\n', E'\n'),
                    'variant', 'important'
                )
                WHEN 'note' THEN jsonb_build_object(
                    'markdown', replace(COALESCE(content, ''), E'\\n', E'\n'),
                    'variant', 'note'
                )
                WHEN 'exception' THEN jsonb_build_object(
                    'markdown', replace(COALESCE(content, ''), E'\\n', E'\n'),
                    'variant', 'warning'
                )
                ELSE jsonb_build_object(
                    'markdown', replace(COALESCE(content, ''), E'\\n', E'\n')
                )
            END,
            jsonb_build_object(
                'legacyType', legacy_type,
                'recoveredBy', '20260725_0006'
            ) || CASE legacy_type
                WHEN 'title' THEN jsonb_build_object('variant', 'heading_1')
                WHEN 'subtitle' THEN jsonb_build_object('variant', 'heading_2')
                WHEN 'link' THEN jsonb_build_object('variant', 'link')
                ELSE '{}'::jsonb
            END,
            "order",
            id,
            now(),
            now()
        FROM missing
        """
    )

    op.execute(
        """
        UPDATE theory_block_v2 AS child
        SET parent_block_id = parent.id
        FROM theory_block AS legacy_child
        JOIN theory_block_v2 AS parent
          ON parent.source_legacy_block_id = legacy_child.parent_id
        WHERE child.source_legacy_block_id = legacy_child.id
          AND legacy_child.parent_id IS NOT NULL
          AND parent.document_version_id = child.document_version_id
          AND child.parent_block_id IS DISTINCT FROM parent.id
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM theory_block_v2
        WHERE settings->>'recoveredBy' = '20260725_0006'
        """
    )
