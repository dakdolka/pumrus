from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.core.tasks.general.entities import TaskItem, Option


@dataclass
class UserMistake:
    id: int
    user_id: int
    task_session_id: int
    mistake_item_id: int
    chosen_option_id: int
    is_resolved: bool = False
    mistake_item: Optional[TaskItem] = None
    chosen_option: Optional[Option] = None
    created_at: Optional[datetime] = None
