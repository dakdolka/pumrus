from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .entities import Task, TaskItem
from app.core.theory.enums import TheorySubject


class ITaskRepository(ABC):
    @abstractmethod
    async def create_task(self, session: AsyncSession, task: Task) -> Task:
        ...

    @abstractmethod
    async def update_task(self, session: AsyncSession, task: Task) -> Task:
        ...

    @abstractmethod
    async def get_task_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        ...

    @abstractmethod
    async def get_tasks_for_subject(
        self, session: AsyncSession, subject_id: int
    ) -> List[Task]:
        ...

    @abstractmethod
    async def replace_task_items(
        self, session: AsyncSession, task_id: int, items: List[TaskItem]
    ) -> None:
        ...
