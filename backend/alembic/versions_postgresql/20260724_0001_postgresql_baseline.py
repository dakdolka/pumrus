"""PostgreSQL baseline with legacy tables and the v2 catalog.

Revision ID: 20260724_0001
Revises:
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260724_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
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


def upgrade() -> None:
    op.create_table(
        "option",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.String(256), nullable=False),
        sa.Column("extras", sa.String(256), nullable=True),
        *timestamp_columns(),
    )
    op.create_table(
        "option_set",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "task_group",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "theory_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
    )
    op.create_table(
        "theory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "task_theory_group",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("is_single", sa.Boolean(), nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.String(256), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("second_name", sa.String(256), nullable=True),
        sa.Column("username", sa.String(256), nullable=True),
        sa.Column("avatar_url", sa.String(256), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        *timestamp_columns(),
    )

    op.create_table(
        "option_set2option",
        sa.Column(
            "option_set_id",
            sa.Integer(),
            sa.ForeignKey("option_set.id"),
            primary_key=True,
        ),
        sa.Column(
            "option_id",
            sa.Integer(),
            sa.ForeignKey("option.id"),
            primary_key=True,
        ),
    )
    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column(
            "task_group_fk",
            sa.Integer(),
            sa.ForeignKey("task_group.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "default_option_set_fk",
            sa.Integer(),
            sa.ForeignKey("option_set.id"),
            nullable=True,
        ),
        sa.Column(
            "trainer_type",
            sa.String(16),
            server_default="options",
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_table(
        "task_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_raw", sa.Text(), nullable=False),
        sa.Column("content_visible", sa.Text(), nullable=False),
        sa.Column("content_correct", sa.Text(), nullable=False),
        sa.Column(
            "correct_option_fk",
            sa.Integer(),
            sa.ForeignKey("option.id"),
            nullable=True,
        ),
        sa.Column(
            "option_set_override_fk",
            sa.Integer(),
            sa.ForeignKey("option_set.id"),
            nullable=True,
        ),
        sa.Column("notice_wrong", sa.Text(), nullable=True),
        sa.Column("notice_right", sa.Text(), nullable=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("task.id"),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_table(
        "task_session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("task.id"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    op.create_table(
        "user_mistakes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_fk",
            sa.Integer(),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column(
            "mistake_item_fk",
            sa.Integer(),
            sa.ForeignKey("task_item.id"),
            nullable=False,
        ),
        sa.Column(
            "chosen_option_fk",
            sa.Integer(),
            sa.ForeignKey("option.id"),
            nullable=True,
        ),
        sa.Column("chosen_option_override", sa.String(256), nullable=True),
        sa.Column(
            "task_session_fk",
            sa.Integer(),
            sa.ForeignKey("task_session.id"),
            nullable=False,
        ),
        sa.Column(
            "is_resolved",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        *timestamp_columns(),
    )
    op.create_table(
        "theory2theory_type",
        sa.Column(
            "theory_id",
            sa.Integer(),
            sa.ForeignKey("theory.id"),
            primary_key=True,
        ),
        sa.Column(
            "type_id",
            sa.Integer(),
            sa.ForeignKey("theory_type.id"),
            primary_key=True,
        ),
    )
    op.create_table(
        "theory_block",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", sa.String(16), nullable=True),
        sa.Column(
            "theory_id",
            sa.Integer(),
            sa.ForeignKey("theory.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("theory_block.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("order", sa.Integer(), server_default="0", nullable=False),
        *timestamp_columns(),
    )
    op.create_table(
        "task_theory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("task_theory_group.id"),
            nullable=True,
        ),
        *timestamp_columns(),
    )
    op.create_table(
        "task_theory2theory",
        sa.Column(
            "theory_id",
            sa.Integer(),
            sa.ForeignKey("theory.id"),
            primary_key=True,
        ),
        sa.Column(
            "task_theory_id",
            sa.Integer(),
            sa.ForeignKey("task_theory.id"),
            primary_key=True,
        ),
        sa.Column("order", sa.Integer(), server_default="0", nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "course_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("course.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "course_id",
            "code",
            name="uq_course_version_code",
        ),
    )
    op.create_index(
        "ix_course_version_course_id",
        "course_version",
        ["course_id"],
    )
    op.create_index(
        "ix_course_version_is_active",
        "course_version",
        ["is_active"],
    )
    op.create_table(
        "topic",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_version_id",
            sa.Integer(),
            sa.ForeignKey("course_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(96), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("short_description", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "course_version_id",
            "code",
            name="uq_topic_code",
        ),
    )
    op.create_index(
        "ix_topic_course_version_id",
        "topic",
        ["course_version_id"],
    )
    op.create_table(
        "exam_task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_version_id",
            sa.Integer(),
            sa.ForeignKey("course_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("short_description", sa.String(1024), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "course_version_id",
            "code",
            name="uq_exam_task_code",
        ),
        sa.UniqueConstraint(
            "course_version_id",
            "number",
            name="uq_exam_task_number",
        ),
    )
    op.create_index(
        "ix_exam_task_course_version_id",
        "exam_task",
        ["course_version_id"],
    )
    op.create_table(
        "exam_task_topic",
        sa.Column(
            "exam_task_id",
            sa.Integer(),
            sa.ForeignKey("exam_task.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topic.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        *timestamp_columns(),
    )


def downgrade() -> None:
    op.drop_table("exam_task_topic")
    op.drop_index("ix_exam_task_course_version_id", table_name="exam_task")
    op.drop_table("exam_task")
    op.drop_index("ix_topic_course_version_id", table_name="topic")
    op.drop_table("topic")
    op.drop_index("ix_course_version_is_active", table_name="course_version")
    op.drop_index("ix_course_version_course_id", table_name="course_version")
    op.drop_table("course_version")
    op.drop_table("task_theory2theory")
    op.drop_table("task_theory")
    op.drop_table("theory_block")
    op.drop_table("theory2theory_type")
    op.drop_table("user_mistakes")
    op.drop_table("task_session")
    op.drop_table("task_item")
    op.drop_table("task")
    op.drop_table("option_set2option")
    op.drop_table("course")
    op.drop_table("user")
    op.drop_table("task_theory_group")
    op.drop_table("theory")
    op.drop_table("theory_type")
    op.drop_table("task_group")
    op.drop_table("option_set")
    op.drop_table("option")
