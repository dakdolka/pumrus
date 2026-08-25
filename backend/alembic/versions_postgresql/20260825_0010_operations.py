"""Add owner settings, media library, audit log and manual entitlements.

Revision ID: 20260825_0010
Revises: 20260825_0009
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260825_0010"
down_revision: Union[str, Sequence[str], None] = "20260825_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(length=96), primary_key=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "media_asset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("original_name", sa.String(length=256), nullable=False),
        sa.Column("storage_name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("content_type", sa.String(length=96), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("alt_text", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_media_asset_status"),
    )
    op.create_index("ix_media_asset_public_id", "media_asset", ["public_id"])
    op.create_index("ix_media_asset_status", "media_asset", ["status"])
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("method", sa.String(length=12), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("remote_address", sa.String(length=96), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admin_audit_log_path", "admin_audit_log", ["path"])
    op.create_table(
        "mistake_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_correct_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'removal_candidate', 'resolved')", name="ck_mistake_queue_status"),
        sa.UniqueConstraint("user_id", "exercise_id", name="uq_mistake_queue_user_exercise"),
    )
    op.create_index("ix_mistake_queue_user_id", "mistake_queue", ["user_id"])
    op.create_index("ix_mistake_queue_exercise_id", "mistake_queue", ["exercise_id"])
    op.create_index("ix_mistake_queue_status", "mistake_queue", ["status"])
    op.alter_column("entitlement", "source_order_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("entitlement", sa.Column("source_type", sa.String(length=16), nullable=False, server_default="payment"))
    op.add_column("entitlement", sa.Column("source_note", sa.String(length=512), nullable=True))
    op.drop_constraint("uq_entitlement_source", "entitlement", type_="unique")
    op.create_unique_constraint(
        "uq_entitlement_payment_source",
        "entitlement",
        ["user_id", "access_policy_id", "source_order_id"],
    )


def downgrade() -> None:
    op.execute("DELETE FROM entitlement WHERE source_order_id IS NULL")
    op.drop_constraint("uq_entitlement_payment_source", "entitlement", type_="unique")
    op.create_unique_constraint(
        "uq_entitlement_source",
        "entitlement",
        ["user_id", "access_policy_id", "source_order_id"],
    )
    op.drop_column("entitlement", "source_note")
    op.drop_column("entitlement", "source_type")
    op.alter_column("entitlement", "source_order_id", existing_type=sa.Integer(), nullable=False)
    op.drop_table("mistake_queue")
    op.drop_table("admin_audit_log")
    op.drop_table("media_asset")
    op.drop_table("app_setting")
