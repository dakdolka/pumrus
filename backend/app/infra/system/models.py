from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import BigInteger, CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class AppSettingBD(TimestampMixin, Base):
    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(96), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    description: Mapped[Optional[str]] = mapped_column(String(512))


class MediaAssetBD(TimestampMixin, Base):
    __tablename__ = "media_asset"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_media_asset_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True)
    original_name: Mapped[str] = mapped_column(String(256))
    storage_name: Mapped[str] = mapped_column(String(128), unique=True)
    content_type: Mapped[str] = mapped_column(String(96))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    alt_text: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)


class AdminAuditLogBD(TimestampMixin, Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    method: Mapped[str] = mapped_column(String(12))
    path: Mapped[str] = mapped_column(String(512), index=True)
    status_code: Mapped[int]
    remote_address: Mapped[Optional[str]] = mapped_column(String(96))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
