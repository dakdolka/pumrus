from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class TaskDocumentBD(TimestampMixin, Base):
    __tablename__ = "task_document"
    __table_args__ = (
        UniqueConstraint("exam_task_id", name="uq_task_document_exam_task"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_task_id: Mapped[int] = mapped_column(
        ForeignKey("exam_task.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256))
    introduction: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft")


class ExerciseBD(TimestampMixin, Base):
    __tablename__ = "exercise"
    __table_args__ = (
        UniqueConstraint(
            "source_legacy_task_item_id",
            name="uq_exercise_legacy_task_item_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_version_id: Mapped[int] = mapped_column(
        ForeignKey("course_version.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="draft")
    difficulty: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[Optional[str]] = mapped_column(String(256))
    source_legacy_task_item_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    published_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "exercise_version.id",
            use_alter=True,
            name="fk_exercise_published_version",
        ),
        nullable=True,
    )

    versions: Mapped[list["ExerciseVersionBD"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        foreign_keys="ExerciseVersionBD.exercise_id",
    )


class ExerciseVersionBD(TimestampMixin, Base):
    __tablename__ = "exercise_version"
    __table_args__ = (
        UniqueConstraint(
            "exercise_id",
            "version_number",
            name="uq_exercise_version",
        ),
        UniqueConstraint(
            "source_legacy_task_item_id",
            name="uq_exercise_version_legacy_task_item_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"),
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    interaction_type: Mapped[str] = mapped_column(String(64))
    response_schema_version: Mapped[int] = mapped_column(Integer, default=1)
    prompt_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    interaction_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    answer_config: Mapped[dict[str, Any]] = mapped_column(JSONB)
    checker_type: Mapped[str] = mapped_column(String(64))
    checker_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    feedback_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_legacy_task_item_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    exercise: Mapped["ExerciseBD"] = relationship(
        back_populates="versions",
        foreign_keys=[exercise_id],
    )


class ExerciseTaskLinkBD(TimestampMixin, Base):
    __tablename__ = "exercise_task_link"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"),
        primary_key=True,
    )
    exam_task_id: Mapped[int] = mapped_column(
        ForeignKey("exam_task.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_primary: Mapped[bool] = mapped_column(default=False)


class ExerciseTopicLinkBD(TimestampMixin, Base):
    __tablename__ = "exercise_topic_link"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_primary: Mapped[bool] = mapped_column(default=False)


class ExerciseSetBD(TimestampMixin, Base):
    __tablename__ = "exercise_set"
    __table_args__ = (
        CheckConstraint(
            "(exam_task_id IS NOT NULL) OR (topic_id IS NOT NULL)",
            name="ck_exercise_set_has_scope",
        ),
        CheckConstraint(
            "access_level IN ('free', 'preview', 'premium')",
            name="ck_exercise_set_access_level",
        ),
        UniqueConstraint(
            "source_legacy_task_id",
            name="uq_exercise_set_legacy_task_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_version_id: Mapped[int] = mapped_column(
        ForeignKey("course_version.id", ondelete="CASCADE"),
        index=True,
    )
    exam_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exam_task.id", ondelete="CASCADE"),
        index=True,
    )
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256))
    access_level: Mapped[str] = mapped_column(
        String(16),
        default="free",
        server_default="free",
    )
    selection_strategy: Mapped[str] = mapped_column(
        String(64),
        default="all_shuffled",
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    source_legacy_task_id: Mapped[Optional[int]] = mapped_column(nullable=True)


class ExerciseSetItemBD(TimestampMixin, Base):
    __tablename__ = "exercise_set_item"
    __table_args__ = (
        UniqueConstraint(
            "exercise_set_id",
            "exercise_id",
            name="uq_exercise_set_item",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_set_id: Mapped[int] = mapped_column(
        ForeignKey("exercise_set.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"),
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    is_preview: Mapped[bool] = mapped_column(
        default=False,
        server_default="false",
    )
