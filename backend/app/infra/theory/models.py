from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Text, Enum
from app.core.db import Base, str_256
from app.core.theory.entities import BlockType, TheoryType

class TheoryBD(Base):
    __tablename__ = 'theory'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    type: Mapped[TheoryType] = mapped_column(Enum(TheoryType))
    blocks: Mapped[List["TheoryBlockBD"]] = relationship(
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