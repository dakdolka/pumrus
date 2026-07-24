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


class TheoryDocumentBD(TimestampMixin, Base):
    __tablename__ = "theory_document"
    __table_args__ = (
        CheckConstraint(
            "(exam_task_id IS NOT NULL) <> (topic_id IS NOT NULL)",
            name="ck_theory_document_single_owner",
        ),
        UniqueConstraint("exam_task_id", name="uq_theory_document_exam_task"),
        UniqueConstraint("topic_id", name="uq_theory_document_topic"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exam_task.id", ondelete="CASCADE"),
        index=True,
    )
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    published_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "theory_document_version.id",
            use_alter=True,
            name="fk_theory_document_published_version",
        ),
        nullable=True,
    )

    versions: Mapped[list["TheoryDocumentVersionBD"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="TheoryDocumentVersionBD.document_id",
    )


class TheoryDocumentVersionBD(TimestampMixin, Base):
    __tablename__ = "theory_document_version"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_theory_document_version",
        ),
        UniqueConstraint(
            "source_legacy_theory_id",
            name="uq_theory_version_legacy_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("theory_document.id", ondelete="CASCADE"),
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    source_legacy_theory_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    document: Mapped["TheoryDocumentBD"] = relationship(
        back_populates="versions",
        foreign_keys=[document_id],
    )
    blocks: Mapped[list["TheoryBlockV2BD"]] = relationship(
        back_populates="document_version",
        cascade="all, delete-orphan",
        foreign_keys="TheoryBlockV2BD.document_version_id",
        order_by="TheoryBlockV2BD.sort_order",
    )


class TheoryBlockV2BD(TimestampMixin, Base):
    __tablename__ = "theory_block_v2"
    __table_args__ = (
        UniqueConstraint(
            "source_legacy_block_id",
            name="uq_theory_block_v2_legacy_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_version_id: Mapped[int] = mapped_column(
        ForeignKey("theory_document_version.id", ondelete="CASCADE"),
        index=True,
    )
    parent_block_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theory_block_v2.id", ondelete="CASCADE"),
        nullable=True,
    )
    block_type: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    source_legacy_block_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    document_version: Mapped["TheoryDocumentVersionBD"] = relationship(
        back_populates="blocks",
        foreign_keys=[document_version_id],
    )
    children: Mapped[list["TheoryBlockV2BD"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped[Optional["TheoryBlockV2BD"]] = relationship(
        back_populates="children",
        remote_side=[id],
    )
