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
        cascade="all, delete-orphan"
    )
    

class TheoryBlockBD(Base):
    __tablename__ = 'theory_text'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[Optional[BlockType]] = mapped_column(Enum(BlockType))
    
    theory_id: Mapped[int] = mapped_column(ForeignKey("theory.id", ondelete="CASCADE"))
    theory: Mapped["TheoryBD"] = relationship(back_populates="blocks")