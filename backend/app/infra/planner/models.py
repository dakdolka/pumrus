from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class StudyPlanBD(TimestampMixin, Base):
    __tablename__ = "study_plan"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_study_plan_request"),
        CheckConstraint("status IN ('active', 'paused')", name="ck_study_plan_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    request_key: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(16), default="active")
    schedule: Mapped[dict] = mapped_column(JSON)


class StudyReminderBD(TimestampMixin, Base):
    __tablename__ = "study_reminder"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_study_reminder_request"),
        CheckConstraint("status IN ('active', 'paused', 'completed')", name="ck_study_reminder_status"),
        CheckConstraint("attempts >= 0", name="ck_study_reminder_attempts"),
        Index("ix_study_reminder_due", "status", "next_notify_at"),
        Index("ix_study_reminder_user_due", "user_id", "due_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("study_plan.id", ondelete="CASCADE"), index=True)
    request_key: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(160))
    target_path: Mapped[str] = mapped_column(String(256))
    timezone: Mapped[str] = mapped_column(String(64))
    # Local wall-clock recurrence; never add 24 hours to a UTC timestamp.
    weekdays: Mapped[list[int]] = mapped_column(JSON, default=list)
    local_time: Mapped[str] = mapped_column(String(5))
    status: Mapped[str] = mapped_column(String(16), default="active")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_notify_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String(24), default="pending")
    attempts: Mapped[int] = mapped_column(default=0)
    lease_token: Mapped[str | None] = mapped_column(String(36))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
