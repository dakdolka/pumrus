"""Add practice access levels and preview membership.

Revision ID: 20260820_0008
Revises: 20260726_0007
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260820_0008"
down_revision: Union[str, Sequence[str], None] = "20260726_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercise_set",
        sa.Column(
            "access_level",
            sa.String(length=16),
            nullable=False,
            server_default="free",
        ),
    )
    op.create_check_constraint(
        "ck_exercise_set_access_level",
        "exercise_set",
        "access_level IN ('free', 'preview', 'premium')",
    )
    op.add_column(
        "exercise_set_item",
        sa.Column(
            "is_preview",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("exercise_set_item", "is_preview")
    op.drop_constraint(
        "ck_exercise_set_access_level",
        "exercise_set",
        type_="check",
    )
    op.drop_column("exercise_set", "access_level")
