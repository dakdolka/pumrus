from re import T
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Text, Enum
import enum
from core.db import Base, str_256

class TheoryType(enum.Enum):
    speechpart = 'speechpart'
    text = 'text'
    
class TextType(enum.Enum):
    text = 'text'
    example = 'example'
    exception = 'exception'
    
class TheoryText(Base):
    __tablename__ = 'theory_text'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[Text]
    type: Mapped[Optional[TextType]] = mapped_column(Enum(TextType))
    
    theory_id: Mapped[int] = mapped_column(ForeignKey("theory.id", ondelete="CASCADE"))
    theory: Mapped["Theory"] = relationship(back_populates="texts")
    
class TheorySVG(Base):
    __tablename__ = "theory_svg"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(256))
    
    theory_id: Mapped[int] = mapped_column(ForeignKey("theory.id", ondelete="CASCADE"))
    theory: Mapped["Theory"] = relationship(back_populates="svgs")
    
class Theory(Base):
    __tablename__ = 'theory'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_256]
    type: Mapped[TheoryType] = mapped_column(Enum(TheoryType))
    texts: Mapped[List["TheoryText"]] = relationship(
        back_populates='theory',
        cascade="all, delete-orphan"
    )
    
    svgs: Mapped[List["TheorySVG"]] = relationship(
        back_populates='theory',
        cascade="all, delete-orphan"
    )
