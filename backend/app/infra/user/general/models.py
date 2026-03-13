from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infra.user.mistakes import UserMistakesBD
from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.core.db import Base, str_256, TimestampMixin



class UserBD(TimestampMixin, Base):
    __tablename__="user"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str_256] = mapped_column(unique=True)
    
    name: Mapped[str_256]
    second_name: Mapped[Optional[str_256]] = mapped_column(default="")
    
    mistakes: Mapped[List["UserMistakesBD"]] = relationship()


    
    