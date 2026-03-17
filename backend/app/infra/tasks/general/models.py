
from typing import List, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, str_256, TimestampMixin
import enum

class TrainerType(str, enum.Enum):
    stress     = "stress"
    dictionary = "dictionary"
    options    = "options"
    input      = "input"


option_set2option = Table(
    "option_set2option",
    Base.metadata,
    Column("option_set_id",Integer, ForeignKey("option_set.id"), primary_key=True),
    Column("option_id", Integer, ForeignKey("option.id"), primary_key=True)
)

class OptionSetBD(TimestampMixin, Base):
    __tablename__ = "option_set"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    options: Mapped[List["OptionBD"]] = relationship(secondary=option_set2option)
    
    
class OptionBD(TimestampMixin, Base):
    __tablename__ = "option"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str_256]
    extras: Mapped[Optional[str_256]]


class TaskGroupBD(TimestampMixin, Base):
    __tablename__ = "task_group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    tasks: Mapped["TaskBD"] = relationship(back_populates="task_group", passive_deletes=True)
    

class TaskBD(TimestampMixin, Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str_256]

    task_group_fk: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_group.id", ondelete="SET NULL"), nullable=True
    )
    task_group: Mapped[Optional["TaskGroupBD"]] = relationship(back_populates="tasks")

    default_option_set_fk: Mapped[Optional[int]] = mapped_column(
        ForeignKey("option_set.id"), nullable=True
    )
    default_option_set: Mapped[Optional["OptionSetBD"]] = relationship()

    items: Mapped[List["TaskItemBD"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    trainer_type: Mapped[TrainerType] = mapped_column(
        SQLEnum(TrainerType, name="trainertype"),
        nullable=False,
        default=TrainerType.options,
        server_default=TrainerType.options.value,
    )


    @property
    def is_active(self) -> bool:
        return bool(self.items)


class TaskItemBD(TimestampMixin, Base):
    __tablename__ = "task_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    content_raw: Mapped[str] = mapped_column(Text, nullable=False)
    content_visible: Mapped[str] = mapped_column(Text, nullable=False)
    content_correct: Mapped[str] = mapped_column(Text, nullable=False)
    
    correct_option_fk: Mapped[Optional[int]] = mapped_column(ForeignKey("option.id"), nullable=True)
    correct_option: Mapped["OptionBD"] = relationship()
    
    option_set_override_fk: Mapped[Optional[int]] = mapped_column(ForeignKey("option_set.id"), nullable=True)
    option_set_override: Mapped["OptionSetBD"] = relationship()
    
    notice_wrong: Mapped[Optional[str]] = mapped_column(Text)
    notice_right: Mapped[Optional[str]] = mapped_column(Text)
    
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id",), nullable=False)
    task: Mapped["TaskBD"] = relationship(back_populates="items")
    
    @property
    def option_set(self) -> "OptionSetBD":
        if self.option_set_override:
            return self.option_set_override
        elif self.task.default_option_set:
            return self.task.default_option_set
        raise ValueError("""Нигде не указан набор опций, отображаемых в элементе задания! 
                         Проверьте TaskItemBD.option_set_override или TaskBD.default_option_set""")
        
    
    def get_notice(self, chosen_option: "OptionBD") -> Optional[str]:
        if chosen_option == self.correct_option:
            return self.notice_right if self.notice_right else None
        return self.notice_wrong if self.notice_wrong else None
    
