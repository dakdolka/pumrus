"""Add PracticeSession v2 and attempts.

Revision ID: 20260724_0004
Revises: 20260724_0003
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260724_0004"
down_revision: Union[str, Sequence[str], None] = "20260724_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def jsonb(name: str) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "practice_session_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "exercise_set_id",
            sa.Integer(),
            sa.ForeignKey("exercise_set.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("mode", sa.String(32), server_default="standard", nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("current_position", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_practice_session_v2_user_id", "practice_session_v2", ["user_id"])
    op.create_index(
        "ix_practice_session_v2_exercise_set_id",
        "practice_session_v2",
        ["exercise_set_id"],
    )
    op.create_index(
        "ix_practice_session_v2_status",
        "practice_session_v2",
        ["status"],
    )

    op.create_table(
        "practice_session_item_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("practice_session_v2.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_version_id",
            sa.Integer(),
            sa.ForeignKey("exercise_version.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(32), server_default="pending", nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "session_id",
            "position",
            name="uq_practice_item_position",
        ),
        sa.UniqueConstraint(
            "session_id",
            "exercise_version_id",
            name="uq_practice_item_exercise_version",
        ),
    )
    op.create_index(
        "ix_practice_session_item_v2_session_id",
        "practice_session_item_v2",
        ["session_id"],
    )
    op.create_index(
        "ix_practice_session_item_v2_exercise_version_id",
        "practice_session_item_v2",
        ["exercise_version_id"],
    )

    op.create_table(
        "attempt_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_item_id",
            sa.Integer(),
            sa.ForeignKey("practice_session_item_v2.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_version_id",
            sa.Integer(),
            sa.ForeignKey("exercise_version.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        jsonb("response_data"),
        jsonb("normalized_response"),
        sa.Column("result_status", sa.String(16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        jsonb("checker_result"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_attempt_v2_user_id", "attempt_v2", ["user_id"])
    op.create_index(
        "ix_attempt_v2_session_item_id",
        "attempt_v2",
        ["session_item_id"],
    )
    op.create_index(
        "ix_attempt_v2_exercise_version_id",
        "attempt_v2",
        ["exercise_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_attempt_v2_exercise_version_id", table_name="attempt_v2")
    op.drop_index("ix_attempt_v2_session_item_id", table_name="attempt_v2")
    op.drop_index("ix_attempt_v2_user_id", table_name="attempt_v2")
    op.drop_table("attempt_v2")
    op.drop_index(
        "ix_practice_session_item_v2_exercise_version_id",
        table_name="practice_session_item_v2",
    )
    op.drop_index(
        "ix_practice_session_item_v2_session_id",
        table_name="practice_session_item_v2",
    )
    op.drop_table("practice_session_item_v2")
    op.drop_index("ix_practice_session_v2_status", table_name="practice_session_v2")
    op.drop_index(
        "ix_practice_session_v2_exercise_set_id",
        table_name="practice_session_v2",
    )
    op.drop_index(
        "ix_practice_session_v2_user_id",
        table_name="practice_session_v2",
    )
    op.drop_table("practice_session_v2")
