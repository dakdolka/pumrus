from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infra.user.mistakes import UserMistakesBD

from datetime import date, datetime
from sqlalchemy import Date, DateTime, Boolean, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.core.db import Base, str_256, TimestampMixin


class UserBD(TimestampMixin, Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str_256] = mapped_column(unique=True)

    name: Mapped[str_256]
    second_name: Mapped[Optional[str_256]] = mapped_column(default="")
    username: Mapped[Optional[str_256]] = mapped_column(default=None)     # @username в tg
    avatar_url: Mapped[Optional[str_256]] = mapped_column(default=None)   # фото профиля

    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)        # бан/мягкое удаление
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # аналитика

    mistakes: Mapped[List["UserMistakesBD"]] = relationship()
