from asyncio import Task
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Text, Enum
from app.core.db import Base, str_256
from app.core.theory.enums import TheoryType, BlockType

theory2theory_type = Table(
    "theory2theory_type",
    Base.metadata,
    Column("theory_id", Integer, ForeignKey("theory.id"), primary_key=True),
    Column("type_id", Integer, ForeignKey("theory_type.id"), primary_key=True),
)

class TaskTheoryAssociation(Base):
    __tablename__ = "task_theory2theory"
    
    theory_id: Mapped[int] = mapped_column(ForeignKey("theory.id"), primary_key=True)
    task_theory_id: Mapped[int] = mapped_column(ForeignKey("task_theory.id"), primary_key=True)
    order: Mapped[int] = mapped_column(default=0)
    
    theory: Mapped["TheoryBD"] = relationship(back_populates="task_associations")
    task: Mapped["TaskTheoryBD"] = relationship(back_populates="theory_associations")

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
    types: Mapped[List["TheoryTypeBD"]] = relationship(
        secondary=theory2theory_type,
        back_populates="theories"
    )
    blocks: Mapped[list["TheoryBlockBD"]] = relationship(
        back_populates='theory',
        order_by="TheoryBlockBD.id",
        cascade="all, delete-orphan"
    )
    task_associations: Mapped[List["TaskTheoryAssociation"]] = relationship(
        back_populates="theory"
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
    

class TaskTheoryGroupBD(Base):
    __tablename__ = "task_theory_group"
    
    id: Mapped[Optional[int]] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    is_single: Mapped[bool]
    tasks_theories: Mapped[List["TaskTheoryBD"]] = relationship(back_populates="group")


class TaskTheoryBD(Base):
    __tablename__ = "task_theory"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_theory_group.id"))
    group: Mapped[Optional["TaskTheoryGroupBD"]] = relationship(back_populates="tasks_theories")
    theory_associations: Mapped[List["TaskTheoryAssociation"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )
