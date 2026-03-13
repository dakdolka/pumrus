from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, TimestampMixin
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
    
    chosen_option_fk: Mapped[int] = mapped_column(ForeignKey("option.id"))
    chosen_option: Mapped["OptionBD"] = relationship()
    
    task_session_fk: Mapped[int] = mapped_column(ForeignKey("task_session.id"))
    task_session: Mapped["TaskSessionBD"] = relationship()