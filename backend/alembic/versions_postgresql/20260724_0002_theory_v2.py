"""Add the versioned theory model.

Revision ID: 20260724_0002
Revises: 20260724_0001
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260724_0002"
down_revision: Union[str, Sequence[str], None] = "20260724_0001"
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
    op.add_column(
        "topic",
        sa.Column("source_legacy_theory_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_topic_legacy_theory_source",
        "topic",
        ["source_legacy_theory_id"],
    )

    op.create_table(
        "theory_document",
        sa.Column("id", sa.Integer(), primary_key=True),
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
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("published_version_id", sa.Integer(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "(exam_task_id IS NOT NULL) <> (topic_id IS NOT NULL)",
            name="ck_theory_document_single_owner",
        ),
        sa.UniqueConstraint(
            "exam_task_id",
            name="uq_theory_document_exam_task",
        ),
        sa.UniqueConstraint(
            "topic_id",
            name="uq_theory_document_topic",
        ),
    )
    op.create_index(
        "ix_theory_document_exam_task_id",
        "theory_document",
        ["exam_task_id"],
    )
    op.create_index(
        "ix_theory_document_topic_id",
        "theory_document",
        ["topic_id"],
    )

    op.create_table(
        "theory_document_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("theory_document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("source_legacy_theory_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_theory_document_version",
        ),
        sa.UniqueConstraint(
            "source_legacy_theory_id",
            name="uq_theory_version_legacy_source",
        ),
    )
    op.create_index(
        "ix_theory_document_version_document_id",
        "theory_document_version",
        ["document_id"],
    )
    op.create_foreign_key(
        "fk_theory_document_published_version",
        "theory_document",
        "theory_document_version",
        ["published_version_id"],
        ["id"],
    )

    op.create_table(
        "theory_block_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.Integer(),
            sa.ForeignKey("theory_document_version.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_block_id",
            sa.Integer(),
            sa.ForeignKey("theory_block_v2.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("block_type", sa.String(32), nullable=False),
        sa.Column(
            "schema_version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("source_legacy_block_id", sa.Integer(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "source_legacy_block_id",
            name="uq_theory_block_v2_legacy_source",
        ),
    )
    op.create_index(
        "ix_theory_block_v2_document_version_id",
        "theory_block_v2",
        ["document_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_theory_block_v2_document_version_id",
        table_name="theory_block_v2",
    )
    op.drop_table("theory_block_v2")
    op.drop_constraint(
        "fk_theory_document_published_version",
        "theory_document",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_theory_document_version_document_id",
        table_name="theory_document_version",
    )
    op.drop_table("theory_document_version")
    op.drop_index(
        "ix_theory_document_topic_id",
        table_name="theory_document",
    )
    op.drop_index(
        "ix_theory_document_exam_task_id",
        table_name="theory_document",
    )
    op.drop_table("theory_document")
    op.drop_constraint(
        "uq_topic_legacy_theory_source",
        "topic",
        type_="unique",
    )
    op.drop_column("topic", "source_legacy_theory_id")
