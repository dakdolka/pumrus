from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.api.tasks.general.schemas import TaskOut


class TaskSessionInitIn(BaseModel):
    user_id: int
    task_id: int


class TaskSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    task_id: int
    is_open: bool
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    task: Optional[TaskOut] = None
