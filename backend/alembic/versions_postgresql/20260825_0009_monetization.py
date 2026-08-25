"""Add products, prices, payments and entitlements.

Revision ID: 20260825_0009
Revises: 20260820_0008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260825_0009"
down_revision: Union[str, Sequence[str], None] = "20260820_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=96), nullable=False, unique=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "access_policy_resource",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("access_policy_id", sa.Integer(), sa.ForeignKey("access_policy.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("resource_type IN ('course_version', 'exam_task', 'topic', 'exercise_set')", name="ck_access_policy_resource_type"),
        sa.UniqueConstraint("access_policy_id", "resource_type", "resource_id", name="uq_access_policy_resource"),
    )
    op.create_index("ix_access_policy_resource_access_policy_id", "access_policy_resource", ["access_policy_id"])
    op.create_index("ix_access_policy_resource_resource_id", "access_policy_resource", ["resource_id"])
    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=96), nullable=False, unique=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("billing_type", sa.String(length=16), nullable=False, server_default="one_time"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("access_policy_id", sa.Integer(), sa.ForeignKey("access_policy.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("billing_type IN ('one_time', 'monthly')", name="ck_product_billing_type"),
        sa.CheckConstraint("status IN ('draft', 'active', 'archived')", name="ck_product_status"),
    )
    op.create_index("ix_product_status", "product", ["status"])
    op.create_table(
        "price",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="yookassa"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_price_positive_amount"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_price_status"),
        sa.UniqueConstraint("product_id", "provider", "currency", name="uq_product_provider_currency"),
    )
    op.create_index("ix_price_product_id", "price", ["product_id"])
    op.create_table(
        "subscription",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price_id", sa.Integer(), sa.ForeignKey("price.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("access_policy_id", sa.Integer(), sa.ForeignKey("access_policy.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="yookassa"),
        sa.Column("payment_method_id", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_charge_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'active', 'past_due', 'cancelled')", name="ck_subscription_status"),
    )
    op.create_index("ix_subscription_user_id", "subscription", ["user_id"])
    op.create_index("ix_subscription_product_id", "subscription", ["product_id"])
    op.create_index("ix_subscription_status", "subscription", ["status"])
    op.create_index("ix_subscription_next_charge_at", "subscription", ["next_charge_at"])
    op.create_table(
        "payment_order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price_id", sa.Integer(), sa.ForeignKey("price.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("invoice_payload", sa.String(length=128), nullable=False, unique=True),
        sa.Column("invoice_url", sa.Text(), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=256), nullable=True, unique=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscription.id", ondelete="SET NULL"), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'paid', 'cancelled', 'expired')", name="ck_payment_order_status"),
    )
    op.create_index("ix_payment_order_public_id", "payment_order", ["public_id"])
    op.create_index("ix_payment_order_user_id", "payment_order", ["user_id"])
    op.create_index("ix_payment_order_product_id", "payment_order", ["product_id"])
    op.create_index("ix_payment_order_status", "payment_order", ["status"])
    op.create_index("ix_payment_order_subscription_id", "payment_order", ["subscription_id"])
    op.create_table(
        "payment_transaction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("payment_order.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_charge_id", sa.String(length=256), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", "provider_charge_id", name="uq_payment_provider_charge"),
    )
    op.create_index("ix_payment_transaction_order_id", "payment_transaction", ["order_id"])
    op.create_table(
        "entitlement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_policy_id", sa.Integer(), sa.ForeignKey("access_policy.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_order_id", sa.Integer(), sa.ForeignKey("payment_order.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'revoked', 'expired')", name="ck_entitlement_status"),
        sa.UniqueConstraint("user_id", "access_policy_id", "source_order_id", name="uq_entitlement_source"),
    )
    op.create_index("ix_entitlement_user_id", "entitlement", ["user_id"])
    op.create_index("ix_entitlement_access_policy_id", "entitlement", ["access_policy_id"])
    op.create_index("ix_entitlement_source_order_id", "entitlement", ["source_order_id"])
    op.create_index("ix_entitlement_status", "entitlement", ["status"])


def downgrade() -> None:
    op.drop_table("entitlement")
    op.drop_table("payment_transaction")
    op.drop_table("payment_order")
    op.drop_table("subscription")
    op.drop_table("price")
    op.drop_table("product")
    op.drop_table("access_policy_resource")
    op.drop_table("access_policy")
