from dataclasses import dataclass, field
from typing import Any, Optional, List

from app.core.theory.enums import TheorySubject
from .enums import TrainerType, InputMode


@dataclass
class TaskItem:
    id: Optional[int]
    task_id: Optional[int]
    order: int
    trainer_type: TrainerType
    raw: str
    visible: str
    correct_option: str
    correct_visible: str
    extra: Optional[dict[str, Any]] = field(default_factory=dict)


@dataclass
class Task:
    id: Optional[int]
    name: str
    subj: TheorySubject
    trainer_type: TrainerType
    input_mode: InputMode
    is_active: bool = True
    items: List[TaskItem] = field(default_factory=list)
