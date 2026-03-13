from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.core.tasks.general.entities import Task


@dataclass
class TaskSession:
    id: int
    user_id: int
    task_id: int
    task: Optional[Task] = None
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @property
    def is_open(self) -> bool:
        return self.closed_at is None
