from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.tasks.general import TaskBD
from app.infra.user.general import UserBD
from app.core.db import Base, TimestampMixin

class TaskSessionBD(TimestampMixin, Base):
    __tablename__="task_session"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))
    user: Mapped["UserBD"] = relationship()
    task: Mapped["TaskBD"] = relationship()
    
    