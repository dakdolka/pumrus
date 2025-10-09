from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Text, Enum
from app.core.db import Base, str_256
import enum


class TheoryType(enum.Enum):
    speechpart = 'speechpart'
    text = 'text'
    wordparts = 'wordparts'
    punctuation = 'punctuation'
    
class BlockType(enum.Enum):
    name = 'name'
    title = 'title'
    subtitle = 'subtitle'
    text = 'text' #Соло для обычных текстов
    rule = 'rule' #Для правила
    example = 'example' #Для примера
    important = 'important'
    exception = 'exception'
    svg = 'svg'
    
    
class Block(Base):
    __tablename__ = 'theory_text'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[Optional[BlockType]] = mapped_column(Enum(BlockType))
    
    theory_id: Mapped[int] = mapped_column(ForeignKey("theory.id", ondelete="CASCADE"))
    theory: Mapped["Theory"] = relationship(back_populates="texts")

    
class Theory(Base):
    __tablename__ = 'theory'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    type: Mapped[TheoryType] = mapped_column(Enum(TheoryType))
    blocks: Mapped[List["Block"]] = relationship(
        back_populates='theory',
        cascade="all, delete-orphan"
    )
