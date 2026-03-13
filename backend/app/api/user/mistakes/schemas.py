from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.api.tasks.general.schemas import TaskItemOut, OptionOut


class UserMistakeCreateIn(BaseModel):
    user_id: int
    task_session_id: int
    mistake_item_id: int
    chosen_option_id: int


class UserMistakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    task_session_id: int
    mistake_item_id: int
    chosen_option_id: int
    is_resolved: bool
    mistake_item: Optional[TaskItemOut] = None
    chosen_option: Optional[OptionOut] = None
    created_at: Optional[datetime] = None
