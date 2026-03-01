from typing import Any, List, Optional

from pydantic import BaseModel

from app.core.tasks.enums import TrainerType, InputMode


class TaskItemDTO(BaseModel):
    id: Optional[int] = None
    order: int
    trainer_type: TrainerType
    raw: str
    visible: str
    correct_option: str
    correct_visible: str
    extra: dict[str, Any] = {}


class TaskBase(BaseModel):
    name: str
    trainer_type: TrainerType
    input_mode: InputMode
    is_active: bool = True


class TaskCreateRequest(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int


class TaskDetailResponse(TaskResponse):
    items: List[TaskItemDTO]


class ParseRawRequest(BaseModel):
    trainer_type: TrainerType
    raw_content: Any  # для STRESS/PREFIX/DICTIONARY: список строк; для SPELLING: список объектов


class ParseRawResponse(BaseModel):
    items: List[TaskItemDTO]
