from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.infra.user.general.models import UserBD


router = APIRouter(prefix="/v2/internal", tags=["v2-internal"])


class TelegramUserSyncIn(BaseModel):
    telegram_id: str = Field(min_length=1, max_length=256)
    first_name: str = Field(min_length=1, max_length=256)
    last_name: str = Field(default="", max_length=256)
    username: str | None = Field(default=None, max_length=256)
    avatar_url: str | None = Field(default=None, max_length=256)


def require_internal(x_internal_key: str | None = Header(default=None)) -> None:
    expected = settings.backend_internal_token
    if not expected:
        raise HTTPException(503, "Internal API is not configured")
    if not x_internal_key or not secrets.compare_digest(x_internal_key, expected):
        raise HTTPException(401, "Invalid internal API key")


@router.post("/telegram-users", dependencies=[Depends(require_internal)])
async def sync_telegram_user(
    body: TelegramUserSyncIn,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(select(UserBD).where(UserBD.tg_id == body.telegram_id))
    created = user is None
    if user is None:
        user = UserBD(
            tg_id=body.telegram_id,
            name=body.first_name,
            second_name=body.last_name,
            username=body.username,
            avatar_url=body.avatar_url,
            is_active=True,
            is_admin=False,
        )
        db.add(user)
    else:
        user.name = body.first_name
        user.second_name = body.last_name
        user.username = body.username
        user.avatar_url = body.avatar_url
    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()
    return {"created": created, "user": {"id": user.id, "telegramId": user.tg_id}}
