from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session_factory
from app.core.payment_service import apply_succeeded_payment, money
from app.infra.monetization.models import (
    PaymentOrderBD,
    PriceBD,
    ProductBD,
    SubscriptionBD,
)
from app.infra.monetization.yookassa import (
    PaymentProviderError,
    yookassa_request,
)


logger = logging.getLogger(__name__)


async def charge_due_subscriptions() -> int:
    if not settings.payments_enabled:
        return 0
    now = datetime.now(timezone.utc)
    processed = 0
    async with async_session_factory() as db:
        for _ in range(50):
            subscription = await db.scalar(
                select(SubscriptionBD)
                .where(
                    SubscriptionBD.status.in_(("active", "past_due")),
                    SubscriptionBD.payment_method_id.is_not(None),
                    SubscriptionBD.next_charge_at.is_not(None),
                    SubscriptionBD.next_charge_at <= now,
                )
                .order_by(SubscriptionBD.next_charge_at, SubscriptionBD.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if subscription is None:
                break
            price = await db.get(PriceBD, subscription.price_id)
            product = await db.get(ProductBD, subscription.product_id)
            if not price or not product or price.status != "active":
                subscription.status = "cancelled"
                subscription.next_charge_at = None
                await db.commit()
                continue
            public_id = str(uuid.uuid4())
            order = PaymentOrderBD(
                public_id=public_id,
                user_id=subscription.user_id,
                product_id=product.id,
                price_id=price.id,
                provider="yookassa",
                amount=price.amount,
                currency="RUB",
                status="pending",
                invoice_payload=public_id,
                subscription_id=subscription.id,
            )
            db.add(order)
            await db.flush()
            # Claim this renewal and persist its order before contacting the
            # provider. A webhook can then finish it after a process restart.
            subscription.next_charge_at = None
            await db.commit()
            try:
                payment = await yookassa_request(
                    "POST",
                    "/payments",
                    payload={
                        "amount": {"value": money(price.amount), "currency": "RUB"},
                        "capture": True,
                        "payment_method_id": subscription.payment_method_id,
                        "description": f"Продление: {product.title}"[:128],
                        "metadata": {"order_id": public_id},
                    },
                    idempotence_key=public_id,
                )
                order.provider_payment_id = payment["id"]
                if payment.get("status") == "succeeded":
                    await apply_succeeded_payment(db, order, payment)
                else:
                    # A pending charge is finalized by the verified webhook.
                    # Do not create a second charge while this one is pending.
                    subscription.next_charge_at = None
                processed += 1
            except PaymentProviderError as error:
                logger.warning(
                    "Recurring payment failed for subscription %s: %s",
                    subscription.id,
                    str(error),
                )
                order.status = "cancelled"
                subscription.status = "past_due"
                subscription.next_charge_at = now + timedelta(days=1)
            await db.commit()
    return processed


async def payment_worker(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await charge_due_subscriptions()
        except Exception:
            logger.exception("Payment worker iteration failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=900)
        except asyncio.TimeoutError:
            pass
