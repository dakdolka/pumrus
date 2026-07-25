"""Repair v2 theory block parent links from imported legacy data.

Revision ID: 20260725_0005
Revises: 20260724_0004
Create Date: 2026-07-25
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260725_0005"
down_revision: Union[str, Sequence[str], None] = "20260724_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    # This migration repairs imported data and intentionally keeps valid links.
    pass
