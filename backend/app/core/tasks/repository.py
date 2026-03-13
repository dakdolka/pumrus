# from abc import ABC, abstractmethod
# from typing import List, Optional

# from sqlalchemy.ext.asyncio import AsyncSession

# from .entities import Task, TaskItem


# class ITaskRepository(ABC):
#     @abstractmethod
#     async def create_task(self, session: AsyncSession, task: Task) -> Task:
#         ...

#     @abstractmethod
#     async def update_task(self, session: AsyncSession, task: Task) -> Task:
#         ...

#     @abstractmethod
#     async def get_task_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]:
#         ...

#     @abstractmethod
#     async def get_all_tasks(self, session: AsyncSession) -> List[Task]:
#         ...

#     @abstractmethod
#     async def replace_task_items(
#         self, session: AsyncSession, task_id: int, items: List[TaskItem]
#     ) -> None:
#         ...
        
#     @abstractmethod
#     async def delete_task_by_id(
#         self, session: AsyncSession, task_id: int
#     ) -> None:
#         ...
