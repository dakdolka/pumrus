from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class PracticeSessionBD(TimestampMixin, Base):
    __tablename__ = "practice_session_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
    )
    exercise_set_id: Mapped[int] = mapped_column(
        ForeignKey("exercise_set.id", ondelete="RESTRICT"),
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(32), default="standard")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    current_position: Mapped[int] = mapped_column(Integer, default=0)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["PracticeSessionItemBD"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PracticeSessionItemBD.position",
    )


class PracticeSessionItemBD(TimestampMixin, Base):
    __tablename__ = "practice_session_item_v2"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_practice_item_position"),
        UniqueConstraint(
            "session_id",
            "exercise_version_id",
            name="uq_practice_item_exercise_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("practice_session_v2.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_version_id: Mapped[int] = mapped_column(
        ForeignKey("exercise_version.id", ondelete="RESTRICT"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(32), default="pending")

    session: Mapped["PracticeSessionBD"] = relationship(back_populates="items")
    attempts: Mapped[list["AttemptV2BD"]] = relationship(
        back_populates="session_item",
        cascade="all, delete-orphan",
    )


class AttemptV2BD(TimestampMixin, Base):
    __tablename__ = "attempt_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
    )
    session_item_id: Mapped[int] = mapped_column(
        ForeignKey("practice_session_item_v2.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_version_id: Mapped[int] = mapped_column(
        ForeignKey("exercise_version.id", ondelete="RESTRICT"),
        index=True,
    )
    response_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    normalized_response: Mapped[dict[str, Any]] = mapped_column(JSONB)
    result_status: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Float)
    checker_result: Mapped[dict[str, Any]] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    session_item: Mapped["PracticeSessionItemBD"] = relationship(
        back_populates="attempts"
    )
