from sqlalchemy import Column, Table, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from typing import Optional, TypedDict
from sqlalchemy import Text, Enum
import enum
import datetime
from core.db import Base, str_256

class Theory(Base):
    __tablename__ = 'theory'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_256] 
    