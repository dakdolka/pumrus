from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Text, Enum
from app.core.db import Base, str_256
from app.core.theory.entities import BlockType
from app.core.theory.enums import TheoryType, TheorySubject

theory2theory_type = Table(
    "theory2theory_type",
    Base.metadata,
    Column("theory_id", Integer, ForeignKey("theory.id"), primary_key=True),
    Column("type_id", Integer, ForeignKey("theory_type.id"), primary_key=True),
)

class TheorySubjectBD(Base):
    __tablename__ = "theory_subject"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[TheorySubject] = mapped_column(Enum(TheorySubject), unique=True)
    theories: Mapped[list["TheoryBD"]] = relationship(
        back_populates="subject"
    )

class TheoryTypeBD(Base):
    __tablename__ = "theory_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[TheoryType] = mapped_column(Enum(TheoryType), unique=True)
    theories: Mapped[list["TheoryBD"]] = relationship(
        secondary=theory2theory_type,
        back_populates="types"
    )


class TheoryBD(Base):
    __tablename__ = "theory"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    subject_id: Mapped[int] = mapped_column(ForeignKey("theory_subject.id"))
    subject: Mapped["TheorySubjectBD"] = relationship(
        back_populates="theories"
    )
    types: Mapped[list["TheoryTypeBD"]] = relationship(
        secondary=theory2theory_type,
        back_populates="theories"
    )

    blocks: Mapped[list["TheoryBlockBD"]] = relationship(
        back_populates='theory',
        order_by="TheoryBlockBD.id",
        cascade="all, delete-orphan"
    )


class TheoryBlockBD(Base):
    __tablename__ = "theory_block"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[Optional[BlockType]] = mapped_column(Enum(BlockType))
    
    theory_id: Mapped[Optional[int]] = mapped_column(ForeignKey("theory.id", ondelete="CASCADE"), nullable=True)
    theory: Mapped["TheoryBD"] = relationship(back_populates="blocks")
    
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("theory_block.id", ondelete="CASCADE"), nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    children: Mapped[List["TheoryBlockBD"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="TheoryBlockBD.order"
    )
    parent: Mapped[Optional["TheoryBlockBD"]] = relationship(back_populates="children", remote_side=[id])