from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.monetization import telegram_user_from_request
from app.core.payment_service import apply_succeeded_payment, money
from app.infra.monetization.models import (
    EntitlementBD,
    PaymentOrderBD,
    PriceBD,
    ProductBD,
    SubscriptionBD,
)
from app.infra.monetization.yookassa import (
    PaymentProviderError,
    yookassa_request,
)


router = APIRouter(prefix="/v2/payments", tags=["v2-payments"])


class CheckoutIn(BaseModel):
    price_id: int


def _payment_status() -> dict[str, Any]:
    return {
        "enabled": settings.payments_enabled,
        "provider": "yookassa",
        "currency": "RUB",
        "termsUrl": settings.payment_terms_url,
        "supportUrl": settings.payment_support_url,
    }


async def _yookassa(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    idempotence_key: str | None = None,
) -> dict[str, Any]:
    try:
        return await yookassa_request(
            method,
            path,
            payload=payload,
            idempotence_key=idempotence_key,
        )
    except PaymentProviderError as error:
        raise HTTPException(502, str(error)) from error


@router.get("/catalog")
async def payment_catalog(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await telegram_user_from_request(request, db, required=False)
    rows = (
        await db.execute(
            select(ProductBD, PriceBD)
            .join(PriceBD, PriceBD.product_id == ProductBD.id)
            .where(
                ProductBD.status == "active",
                PriceBD.status == "active",
                PriceBD.provider == "yookassa",
            )
            .order_by(PriceBD.amount, ProductBD.id)
        )
    ).all()
    now = datetime.now(timezone.utc)
    active_policy_ids: set[int] = set()
    subscriptions: list[SubscriptionBD] = []
    if user is not None:
        active_policy_ids = set((await db.scalars(
            select(EntitlementBD.access_policy_id).where(
                EntitlementBD.user_id == user.id,
                EntitlementBD.status == "active",
                EntitlementBD.starts_at <= now,
                or_(EntitlementBD.ends_at.is_(None), EntitlementBD.ends_at > now),
            )
        )).all())
        subscriptions = list((await db.scalars(
            select(SubscriptionBD).where(
                SubscriptionBD.user_id == user.id,
                SubscriptionBD.status.in_(("pending", "active", "past_due")),
            )
        )).all())
    subscription_by_product = {item.product_id: item for item in subscriptions}
    return {
        **_payment_status(),
        "products": [
            {
                "id": product.id,
                "code": product.code,
                "title": product.title,
                "description": product.description,
                "billingType": product.billing_type,
                "owned": product.access_policy_id in active_policy_ids,
                "subscription": (
                    {
                        "id": subscription_by_product[product.id].id,
                        "status": subscription_by_product[product.id].status,
                        "currentPeriodEnd": subscription_by_product[product.id].current_period_end,
                    }
                    if product.id in subscription_by_product else None
                ),
                "price": {
                    "id": price.id,
                    "amount": price.amount,
                    "currency": price.currency,
                },
            }
            for product, price in rows
        ],
    }


@router.post("/checkout", status_code=201)
async def create_checkout(
    body: CheckoutIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not settings.payments_enabled:
        raise HTTPException(503, "Оплата пока не включена")
    user = await telegram_user_from_request(request, db, required=True)
    row = (
        await db.execute(
            select(PriceBD, ProductBD)
            .join(ProductBD, ProductBD.id == PriceBD.product_id)
            .where(
                PriceBD.id == body.price_id,
                PriceBD.status == "active",
                PriceBD.provider == "yookassa",
                PriceBD.currency == "RUB",
                ProductBD.status == "active",
            )
        )
    ).first()
    if row is None:
        raise HTTPException(404, "Предложение больше недоступно")
    price, product = row
    now = datetime.now(timezone.utc)
    owned = await db.scalar(select(EntitlementBD.id).where(
        EntitlementBD.user_id == user.id,
        EntitlementBD.access_policy_id == product.access_policy_id,
        EntitlementBD.status == "active",
        EntitlementBD.starts_at <= now,
        or_(EntitlementBD.ends_at.is_(None), EntitlementBD.ends_at > now),
    ))
    if owned is not None and product.billing_type == "one_time":
        raise HTTPException(409, "Этот доступ уже куплен")
    pending_order = await db.scalar(
        select(PaymentOrderBD)
        .where(
            PaymentOrderBD.user_id == user.id,
            PaymentOrderBD.product_id == product.id,
            PaymentOrderBD.status == "pending",
            PaymentOrderBD.invoice_url.is_not(None),
            PaymentOrderBD.created_at > now - timedelta(minutes=30),
        )
        .order_by(PaymentOrderBD.id.desc())
    )
    if pending_order is not None:
        return {
            "orderId": pending_order.public_id,
            "confirmationUrl": pending_order.invoice_url,
            "provider": pending_order.provider,
        }
    subscription = None
    if product.billing_type == "monthly":
        subscription = await db.scalar(select(SubscriptionBD).where(
            SubscriptionBD.user_id == user.id,
            SubscriptionBD.product_id == product.id,
            SubscriptionBD.status.in_(("pending", "active", "past_due")),
        ))
        if subscription is not None and subscription.status == "active":
            raise HTTPException(409, "Подписка уже активна")
        if subscription is None:
            subscription = SubscriptionBD(
                user_id=user.id,
                product_id=product.id,
                price_id=price.id,
                access_policy_id=product.access_policy_id,
                provider="yookassa",
                status="pending",
            )
            db.add(subscription)
            await db.flush()
    public_id = str(uuid.uuid4())
    order = PaymentOrderBD(
        public_id=public_id,
        user_id=user.id,
        product_id=product.id,
        price_id=price.id,
        provider="yookassa",
        amount=price.amount,
        currency="RUB",
        status="pending",
        invoice_payload=public_id,
        subscription_id=subscription.id if subscription else None,
    )
    db.add(order)
    await db.flush()
    return_separator = "&" if "?" in settings.payment_return_url else "?"
    payment_data: dict[str, Any] = {
        "amount": {"value": money(price.amount), "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": (
                f"{settings.payment_return_url}{return_separator}order={public_id}"
            ),
        },
        "description": product.title[:128],
        "metadata": {"order_id": public_id},
    }
    if product.billing_type == "monthly":
        payment_data["save_payment_method"] = True
    # Persist the merchant-side order before the external call. If the process
    # stops after ЮKassa accepts the payment, the webhook can still resolve it
    # by the order id stored in metadata.
    await db.commit()
    try:
        payment = await _yookassa(
            "POST",
            "/payments",
            payload=payment_data,
            idempotence_key=public_id,
        )
    except HTTPException:
        order.status = "cancelled"
        await db.commit()
        raise
    order.provider_payment_id = payment["id"]
    order.invoice_url = payment.get("confirmation", {}).get("confirmation_url")
    if not order.invoice_url:
        order.status = "cancelled"
        await db.commit()
        raise HTTPException(502, "ЮKassa не вернула страницу оплаты")
    await db.commit()
    return {
        "orderId": order.public_id,
        "confirmationUrl": order.invoice_url,
        "provider": order.provider,
    }


@router.post("/webhooks/yookassa")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    notice = await request.json()
    payment_id = str((notice.get("object") or {}).get("id") or "")
    if not payment_id:
        raise HTTPException(422, "Payment id is missing")
    # The notification body is not trusted. Fetching the payment with merchant
    # credentials verifies both its status and the amount recorded by ЮKassa.
    payment = await _yookassa("GET", f"/payments/{payment_id}")
    order_public_id = str((payment.get("metadata") or {}).get("order_id") or "")
    order = await db.scalar(
        select(PaymentOrderBD)
        .where(or_(
            PaymentOrderBD.provider_payment_id == payment_id,
            PaymentOrderBD.public_id == order_public_id,
        ))
        .with_for_update()
    )
    if order is None:
        raise HTTPException(404, "Order not found")
    amount = payment.get("amount") or {}
    if amount.get("currency") != order.currency or amount.get("value") != money(order.amount):
        raise HTTPException(409, "Payment amount does not match the order")
    if payment.get("status") == "succeeded":
        await apply_succeeded_payment(db, order, payment)
    elif payment.get("status") == "canceled":
        order.status = "cancelled"
        if order.subscription_id:
            subscription = await db.get(SubscriptionBD, order.subscription_id)
            if subscription is not None:
                if subscription.status == "pending":
                    subscription.status = "cancelled"
                    subscription.cancelled_at = datetime.now(timezone.utc)
                else:
                    subscription.status = "past_due"
                    subscription.next_charge_at = (
                        datetime.now(timezone.utc) + timedelta(days=1)
                    )
    await db.commit()
    return {"ok": True}


@router.get("/orders/{order_public_id}")
async def payment_order_status(
    order_public_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await telegram_user_from_request(request, db, required=True)
    order = await db.scalar(select(PaymentOrderBD).where(
        PaymentOrderBD.public_id == order_public_id,
        PaymentOrderBD.user_id == user.id,
    ))
    if order is None:
        raise HTTPException(404, "Заказ не найден")
    return {"orderId": order.public_id, "status": order.status}


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await telegram_user_from_request(request, db, required=True)
    subscription = await db.scalar(select(SubscriptionBD).where(
        SubscriptionBD.id == subscription_id,
        SubscriptionBD.user_id == user.id,
    ))
    if subscription is None:
        raise HTTPException(404, "Подписка не найдена")
    subscription.status = "cancelled"
    subscription.payment_method_id = None
    subscription.next_charge_at = None
    subscription.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    return {"cancelled": True, "accessUntil": subscription.current_period_end}
