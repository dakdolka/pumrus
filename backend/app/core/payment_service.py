from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.monetization.models import (
    EntitlementBD,
    PaymentOrderBD,
    PaymentTransactionBD,
    ProductBD,
    SubscriptionBD,
)


def money(amount: int) -> str:
    return f"{Decimal(amount) / 100:.2f}"


async def apply_succeeded_payment(
    db: AsyncSession,
    order: PaymentOrderBD,
    payment: dict[str, Any],
) -> None:
    charge_id = payment["id"]
    existing = await db.scalar(select(PaymentTransactionBD).where(
        PaymentTransactionBD.provider == "yookassa",
        PaymentTransactionBD.provider_charge_id == charge_id,
    ))
    if existing is not None:
        return
    now = datetime.now(timezone.utc)
    product = await db.get(ProductBD, order.product_id)
    if product is None:
        raise RuntimeError("Продукт заказа не найден")
    period_end = None
    if product.billing_type == "monthly":
        existing_entitlement = await db.scalar(select(EntitlementBD).where(
            EntitlementBD.user_id == order.user_id,
            EntitlementBD.access_policy_id == product.access_policy_id,
            EntitlementBD.status == "active",
            EntitlementBD.source_type == "payment",
        ).order_by(EntitlementBD.id.desc()))
        period_start = (
            existing_entitlement.ends_at
            if existing_entitlement is not None
            and existing_entitlement.ends_at is not None
            and existing_entitlement.ends_at > now
            else now
        )
        period_end = period_start + timedelta(days=30)
    db.add(PaymentTransactionBD(
        order_id=order.id,
        provider="yookassa",
        provider_charge_id=charge_id,
        amount=order.amount,
        currency=order.currency,
        subscription_expires_at=period_end,
        raw_data={
            "status": payment.get("status"),
            "paid": payment.get("paid"),
            "captured": payment.get("captured"),
            "paymentMethod": {
                "type": (payment.get("payment_method") or {}).get("type"),
                "saved": (payment.get("payment_method") or {}).get("saved"),
            },
            "metadata": payment.get("metadata") or {},
        },
    ))
    entitlement = await db.scalar(select(EntitlementBD).where(
        EntitlementBD.user_id == order.user_id,
        EntitlementBD.access_policy_id == product.access_policy_id,
        EntitlementBD.status == "active",
        EntitlementBD.source_type == "payment",
    ).order_by(EntitlementBD.id.desc()))
    if entitlement is None:
        entitlement = EntitlementBD(
            user_id=order.user_id,
            access_policy_id=product.access_policy_id,
            source_order_id=order.id,
            source_type="payment",
            status="active",
            starts_at=now,
            ends_at=period_end,
        )
        db.add(entitlement)
    else:
        entitlement.ends_at = period_end
    order.status = "paid"
    order.paid_at = now
    if order.subscription_id:
        subscription = await db.get(SubscriptionBD, order.subscription_id)
        payment_method = payment.get("payment_method") or {}
        if subscription:
            subscription.status = "active"
            subscription.payment_method_id = (
                payment_method.get("id") if payment_method.get("saved") else None
            )
            subscription.current_period_end = period_end
            subscription.next_charge_at = (
                period_end if subscription.payment_method_id else None
            )
