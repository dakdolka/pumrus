from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class AccessPolicyBD(TimestampMixin, Base):
    __tablename__ = "access_policy"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(96), unique=True)
    title: Mapped[str] = mapped_column(String(256))


class AccessPolicyResourceBD(TimestampMixin, Base):
    __tablename__ = "access_policy_resource"
    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('course_version', 'exam_task', 'topic', 'exercise_set')",
            name="ck_access_policy_resource_type",
        ),
        UniqueConstraint(
            "access_policy_id",
            "resource_type",
            "resource_id",
            name="uq_access_policy_resource",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    access_policy_id: Mapped[int] = mapped_column(
        ForeignKey("access_policy.id", ondelete="CASCADE"),
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[int] = mapped_column(Integer, index=True)


class ProductBD(TimestampMixin, Base):
    __tablename__ = "product"
    __table_args__ = (
        CheckConstraint(
            "billing_type IN ('one_time', 'monthly')",
            name="ck_product_billing_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="ck_product_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(96), unique=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    billing_type: Mapped[str] = mapped_column(String(16), default="one_time")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    access_policy_id: Mapped[int] = mapped_column(
        ForeignKey("access_policy.id", ondelete="RESTRICT"),
        unique=True,
    )


class PriceBD(TimestampMixin, Base):
    __tablename__ = "price"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_price_positive_amount"),
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_price_status",
        ),
        UniqueConstraint(
            "product_id",
            "provider",
            "currency",
            name="uq_product_provider_currency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), default="yookassa")
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="active")


class PaymentOrderBD(TimestampMixin, Base):
    __tablename__ = "payment_order"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'cancelled', 'expired')",
            name="ck_payment_order_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"),
        index=True,
    )
    price_id: Mapped[int] = mapped_column(
        ForeignKey("price.id", ondelete="RESTRICT"),
    )
    provider: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    invoice_payload: Mapped[str] = mapped_column(String(128), unique=True)
    invoice_url: Mapped[Optional[str]] = mapped_column(Text)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(256),
        unique=True,
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subscription.id", ondelete="SET NULL"),
        index=True,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class PaymentTransactionBD(TimestampMixin, Base):
    __tablename__ = "payment_transaction"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_charge_id",
            name="uq_payment_provider_charge",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("payment_order.id", ondelete="RESTRICT"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32))
    provider_charge_id: Mapped[str] = mapped_column(String(256))
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class EntitlementBD(TimestampMixin, Base):
    __tablename__ = "entitlement"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'revoked', 'expired')",
            name="ck_entitlement_status",
        ),
        UniqueConstraint(
            "user_id",
            "access_policy_id",
            "source_order_id",
            name="uq_entitlement_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    access_policy_id: Mapped[int] = mapped_column(
        ForeignKey("access_policy.id", ondelete="RESTRICT"),
        index=True,
    )
    source_order_id: Mapped[int] = mapped_column(
        ForeignKey("payment_order.id", ondelete="RESTRICT"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class SubscriptionBD(TimestampMixin, Base):
    __tablename__ = "subscription"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'past_due', 'cancelled')",
            name="ck_subscription_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"),
        index=True,
    )
    price_id: Mapped[int] = mapped_column(
        ForeignKey("price.id", ondelete="RESTRICT"),
    )
    access_policy_id: Mapped[int] = mapped_column(
        ForeignKey("access_policy.id", ondelete="RESTRICT"),
    )
    provider: Mapped[str] = mapped_column(String(32), default="yookassa")
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    next_charge_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
