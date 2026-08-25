from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


YOOKASSA_API = "https://api.yookassa.ru/v3"


class PaymentProviderError(RuntimeError):
    pass


async def yookassa_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    idempotence_key: str | None = None,
) -> dict[str, Any]:
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        raise PaymentProviderError("ЮKassa не настроена")
    headers = {"Content-Type": "application/json"}
    if idempotence_key:
        headers["Idempotence-Key"] = idempotence_key
    try:
        async with httpx.AsyncClient(
            auth=(settings.yookassa_shop_id, settings.yookassa_secret_key),
            timeout=20,
        ) as client:
            response = await client.request(
                method,
                f"{YOOKASSA_API}{path}",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as error:
        raise PaymentProviderError(
            "Платёжный провайдер временно недоступен"
        ) from error
    try:
        result = response.json()
    except ValueError as error:
        raise PaymentProviderError(
            "Платёжный провайдер вернул некорректный ответ"
        ) from error
    if not response.is_success:
        raise PaymentProviderError(
            result.get("description") or "Платёжный провайдер временно недоступен"
        )
    return result
