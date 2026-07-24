from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class CourseBD(TimestampMixin, Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="draft")

    versions: Mapped[list["CourseVersionBD"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


class CourseVersionBD(TimestampMixin, Base):
    __tablename__ = "course_version"
    __table_args__ = (
        UniqueConstraint("course_id", "code", name="uq_course_version_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    course: Mapped["CourseBD"] = relationship(back_populates="versions")
    exam_tasks: Mapped[list["ExamTaskBD"]] = relationship(
        back_populates="course_version",
        cascade="all, delete-orphan",
    )


class ExamTaskBD(TimestampMixin, Base):
    __tablename__ = "exam_task"
    __table_args__ = (
        UniqueConstraint("course_version_id", "code", name="uq_exam_task_code"),
        UniqueConstraint("course_version_id", "number", name="uq_exam_task_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_version_id: Mapped[int] = mapped_column(
        ForeignKey("course_version.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(256))
    short_description: Mapped[Optional[str]] = mapped_column(String(1024))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="draft")

    course_version: Mapped["CourseVersionBD"] = relationship(back_populates="exam_tasks")
    topic_links: Mapped[list["ExamTaskTopicBD"]] = relationship(
        back_populates="exam_task",
        cascade="all, delete-orphan",
        order_by="ExamTaskTopicBD.sort_order",
    )


class TopicBD(TimestampMixin, Base):
    __tablename__ = "topic"
    __table_args__ = (
        UniqueConstraint("course_version_id", "code", name="uq_topic_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_version_id: Mapped[int] = mapped_column(
        ForeignKey("course_version.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(96))
    title: Mapped[str] = mapped_column(String(256))
    short_description: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="draft")

    task_links: Mapped[list["ExamTaskTopicBD"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class ExamTaskTopicBD(TimestampMixin, Base):
    __tablename__ = "exam_task_topic"

    exam_task_id: Mapped[int] = mapped_column(
        ForeignKey("exam_task.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    exam_task: Mapped["ExamTaskBD"] = relationship(back_populates="topic_links")
    topic: Mapped["TopicBD"] = relationship(back_populates="task_links")
