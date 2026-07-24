"""Add the versioned exercise bank.

Revision ID: 20260724_0003
Revises: 20260724_0002
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260724_0003"
down_revision: Union[str, Sequence[str], None] = "20260724_0002"
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


def jsonb(name: str, *, empty: bool = False) -> sa.Column:
    kwargs = {"nullable": False}
    if empty:
        kwargs["server_default"] = sa.text("'{}'::jsonb")
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        **kwargs,
    )


def upgrade() -> None:
    op.create_table(
        "task_document",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "exam_task_id",
            sa.Integer(),
            sa.ForeignKey("exam_task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(256), nullable=False),
        jsonb("introduction", empty=True),
        jsonb("configuration", empty=True),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        *timestamps(),
        sa.UniqueConstraint("exam_task_id", name="uq_task_document_exam_task"),
    )
    op.create_index("ix_task_document_exam_task_id", "task_document", ["exam_task_id"])

    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_version_id",
            sa.Integer(),
            sa.ForeignKey("course_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(256), nullable=True),
        sa.Column("source_legacy_task_item_id", sa.Integer(), nullable=True),
        sa.Column("published_version_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "source_legacy_task_item_id",
            name="uq_exercise_legacy_task_item_source",
        ),
    )
    op.create_index("ix_exercise_course_version_id", "exercise", ["course_version_id"])

    op.create_table(
        "exercise_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("interaction_type", sa.String(64), nullable=False),
        sa.Column(
            "response_schema_version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        jsonb("prompt_data"),
        jsonb("interaction_config", empty=True),
        jsonb("answer_config"),
        sa.Column("checker_type", sa.String(64), nullable=False),
        jsonb("checker_config", empty=True),
        jsonb("feedback_data", empty=True),
        sa.Column("source_legacy_task_item_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "exercise_id",
            "version_number",
            name="uq_exercise_version",
        ),
        sa.UniqueConstraint(
            "source_legacy_task_item_id",
            name="uq_exercise_version_legacy_task_item_source",
        ),
    )
    op.create_index(
        "ix_exercise_version_exercise_id",
        "exercise_version",
        ["exercise_id"],
    )
    op.create_foreign_key(
        "fk_exercise_published_version",
        "exercise",
        "exercise_version",
        ["published_version_id"],
        ["id"],
    )

    op.create_table(
        "exercise_task_link",
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "exam_task_id",
            sa.Integer(),
            sa.ForeignKey("exam_task.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "exercise_topic_link",
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topic.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "exercise_set",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_version_id",
            sa.Integer(),
            sa.ForeignKey("course_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exam_task_id",
            sa.Integer(),
            sa.ForeignKey("exam_task.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topic.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column(
            "selection_strategy",
            sa.String(64),
            server_default="all_shuffled",
            nullable=False,
        ),
        jsonb("configuration", empty=True),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("source_legacy_task_id", sa.Integer(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "source_legacy_task_id",
            name="uq_exercise_set_legacy_task_source",
        ),
        sa.CheckConstraint(
            "(exam_task_id IS NOT NULL) OR (topic_id IS NOT NULL)",
            name="ck_exercise_set_has_scope",
        ),
    )
    op.create_index(
        "ix_exercise_set_course_version_id",
        "exercise_set",
        ["course_version_id"],
    )
    op.create_index("ix_exercise_set_exam_task_id", "exercise_set", ["exam_task_id"])
    op.create_index("ix_exercise_set_topic_id", "exercise_set", ["topic_id"])
    op.create_table(
        "exercise_set_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "exercise_set_id",
            sa.Integer(),
            sa.ForeignKey("exercise_set.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "exercise_set_id",
            "exercise_id",
            name="uq_exercise_set_item",
        ),
    )
    op.create_index(
        "ix_exercise_set_item_exercise_set_id",
        "exercise_set_item",
        ["exercise_set_id"],
    )
    op.create_index(
        "ix_exercise_set_item_exercise_id",
        "exercise_set_item",
        ["exercise_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_exercise_set_item_exercise_id", table_name="exercise_set_item")
    op.drop_index(
        "ix_exercise_set_item_exercise_set_id",
        table_name="exercise_set_item",
    )
    op.drop_table("exercise_set_item")
    op.drop_index("ix_exercise_set_topic_id", table_name="exercise_set")
    op.drop_index("ix_exercise_set_exam_task_id", table_name="exercise_set")
    op.drop_index("ix_exercise_set_course_version_id", table_name="exercise_set")
    op.drop_table("exercise_set")
    op.drop_table("exercise_topic_link")
    op.drop_table("exercise_task_link")
    op.drop_constraint(
        "fk_exercise_published_version",
        "exercise",
        type_="foreignkey",
    )
    op.drop_index("ix_exercise_version_exercise_id", table_name="exercise_version")
    op.drop_table("exercise_version")
    op.drop_index("ix_exercise_course_version_id", table_name="exercise")
    op.drop_table("exercise")
    op.drop_index("ix_task_document_exam_task_id", table_name="task_document")
    op.drop_table("task_document")
