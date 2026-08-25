from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infra.exercises.models import ExerciseSetBD
from app.infra.monetization.models import (
    AccessPolicyResourceBD,
    EntitlementBD,
    PriceBD,
    ProductBD,
)
from app.infra.user.general.models import UserBD


def validate_telegram_init_data(raw_data: str) -> dict:
    if not settings.telegram_bot_token:
        raise HTTPException(503, "Telegram authentication is not configured")
    values = dict(parse_qsl(raw_data, keep_blank_values=True))
    received_hash = values.pop("hash", "")
    if not received_hash:
        raise HTTPException(401, "Telegram authentication is required")
    check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode(),
        hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(received_hash, expected_hash):
        raise HTTPException(401, "Invalid Telegram authentication")
    try:
        auth_date = int(values.get("auth_date", "0"))
    except ValueError as error:
        raise HTTPException(401, "Invalid Telegram authentication date") from error
    if auth_date <= 0 or time.time() - auth_date > settings.telegram_init_data_max_age:
        raise HTTPException(401, "Telegram authentication has expired")
    try:
        user = json.loads(values.get("user", "{}"))
    except json.JSONDecodeError as error:
        raise HTTPException(401, "Invalid Telegram user data") from error
    if not user.get("id"):
        raise HTTPException(401, "Telegram user is missing")
    return user


async def telegram_user_from_request(
    request: Request,
    db: AsyncSession,
    *,
    required: bool = False,
) -> UserBD | None:
    raw_data = request.headers.get("X-Telegram-Init-Data", "")
    if not raw_data:
        if required:
            raise HTTPException(401, "Для покупки нужно войти через Telegram")
        return None
    telegram_user = validate_telegram_init_data(raw_data)
    user = await db.scalar(
        select(UserBD).where(UserBD.tg_id == str(telegram_user["id"]))
    )
    if user is None:
        if required:
            raise HTTPException(404, "Сначала запустите бота командой /start")
        return None
    return user


async def user_has_resource_access(
    db: AsyncSession,
    user_id: int | None,
    resource_type: str,
    resource_id: int,
) -> bool:
    if user_id is None:
        return False
    now = datetime.now(timezone.utc)
    result = await db.scalar(
        select(EntitlementBD.id)
        .join(
            AccessPolicyResourceBD,
            AccessPolicyResourceBD.access_policy_id
            == EntitlementBD.access_policy_id,
        )
        .where(
            EntitlementBD.user_id == user_id,
            EntitlementBD.status == "active",
            EntitlementBD.starts_at <= now,
            or_(EntitlementBD.ends_at.is_(None), EntitlementBD.ends_at > now),
            AccessPolicyResourceBD.resource_type == resource_type,
            AccessPolicyResourceBD.resource_id == resource_id,
        )
        .limit(1)
    )
    return result is not None


async def user_has_exercise_set_access(
    db: AsyncSession,
    user_id: int | None,
    exercise_set: ExerciseSetBD,
) -> bool:
    if exercise_set.access_level == "free":
        return True
    if exercise_set.access_level == "preview":
        return False
    scopes = [("exercise_set", exercise_set.id)]
    if exercise_set.topic_id is not None:
        scopes.append(("topic", exercise_set.topic_id))
    if exercise_set.exam_task_id is not None:
        scopes.append(("exam_task", exercise_set.exam_task_id))
    scopes.append(("course_version", exercise_set.course_version_id))
    for resource_type, resource_id in scopes:
        if await user_has_resource_access(db, user_id, resource_type, resource_id):
            return True
    return False


async def product_offer_for_exercise_set(
    db: AsyncSession,
    exercise_set: ExerciseSetBD,
) -> dict | None:
    resource_conditions = [
        and_(
            AccessPolicyResourceBD.resource_type == "exercise_set",
            AccessPolicyResourceBD.resource_id == exercise_set.id,
        ),
        and_(
            AccessPolicyResourceBD.resource_type == "exam_task",
            AccessPolicyResourceBD.resource_id == exercise_set.exam_task_id,
        ),
        and_(
            AccessPolicyResourceBD.resource_type == "course_version",
            AccessPolicyResourceBD.resource_id == exercise_set.course_version_id,
        ),
    ]
    if exercise_set.topic_id is not None:
        resource_conditions.append(and_(
            AccessPolicyResourceBD.resource_type == "topic",
            AccessPolicyResourceBD.resource_id == exercise_set.topic_id,
        ))
    row = (
        await db.execute(
            select(ProductBD, PriceBD)
            .join(
                AccessPolicyResourceBD,
                AccessPolicyResourceBD.access_policy_id
                == ProductBD.access_policy_id,
            )
            .join(PriceBD, PriceBD.product_id == ProductBD.id)
            .where(
                ProductBD.status == "active",
                PriceBD.status == "active",
                PriceBD.provider == "yookassa",
                or_(*resource_conditions),
            )
            .order_by(PriceBD.amount, ProductBD.id)
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    product, price = row
    return {
        "productId": product.id,
        "priceId": price.id,
        "title": product.title,
        "description": product.description,
        "billingType": product.billing_type,
        "amount": price.amount,
        "currency": price.currency,
        "checkoutEnabled": settings.payments_enabled,
    }
