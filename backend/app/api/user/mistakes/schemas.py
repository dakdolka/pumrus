from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.api.tasks.general.schemas import TaskItemOut, OptionOut


class UserMistakeCreateIn(BaseModel):
    user_id: int
    task_session_id: int
    mistake_item_id: int
    chosen_option_id: Optional[int]
    chosen_option_override: Optional[str] = None


class UserMistakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    task_session_id: int
    mistake_item_id: int
    is_resolved: bool
    chosen_option_id: Optional[int] = None
    mistake_item: Optional[TaskItemOut] = None
    chosen_option: Optional[OptionOut] = None
    chosen_option_override: Optional[str] = None
    created_at: Optional[datetime] = None
