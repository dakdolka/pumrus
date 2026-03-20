from typing import Optional
from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, TimestampMixin, str_256
from app.infra.user.general import UserBD
from app.infra.tasks.general import TaskItemBD, OptionBD
from app.infra.tasks.sessions import TaskSessionBD

class UserMistakesBD(TimestampMixin, Base):
    __tablename__="user_mistakes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    user_fk: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user : Mapped["UserBD"] = relationship(back_populates="mistakes")
    
    mistake_item_fk: Mapped[int] = mapped_column(ForeignKey("task_item.id"))
    mistake_item: Mapped["TaskItemBD"] = relationship()
    
    chosen_option_fk: Mapped[Optional[int]] = mapped_column(ForeignKey("option.id"), default=None)
    chosen_option: Mapped[Optional["OptionBD"]] = relationship()
    chosen_option_override: Mapped[Optional[str_256]]
    
    task_session_fk: Mapped[int] = mapped_column(ForeignKey("task_session.id"))
    task_session: Mapped["TaskSessionBD"] = relationship()
    
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)