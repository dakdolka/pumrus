from typing import List, Optional

from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TaskBD(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    trainer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    input_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[List["TaskItemBD"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskItemBD.item_order",
    )


class TaskItemBD(Base):
    __tablename__ = "task_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    item_order: Mapped[int] = mapped_column(Integer, nullable=False)

    trainer_type: Mapped[str] = mapped_column(String(32), nullable=False)

    raw: Mapped[str] = mapped_column(Text, nullable=False)
    visible: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option: Mapped[str] = mapped_column(Text, nullable=False)
    correct_visible: Mapped[str] = mapped_column(Text, nullable=False)

    extra_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    task: Mapped["TaskBD"] = relationship(back_populates="items")
