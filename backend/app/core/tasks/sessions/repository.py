from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import TaskSession


class ITaskSessionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession,
                        session_id: int) -> Optional[TaskSession]: ...

    @abstractmethod
    async def get_by_user_and_task(self, session: AsyncSession,
                                   user_id: int, task_id: int) -> Optional[TaskSession]: ...

    @abstractmethod
    async def get_all_by_user(self, session: AsyncSession,
                               user_id: int) -> List[TaskSession]: ...

    @abstractmethod
    async def create(self, session: AsyncSession,
                     user_id: int, task_id: int) -> TaskSession: ...

    @abstractmethod
    async def close(self, session: AsyncSession,
                    session_id: int, closed_at: datetime) -> TaskSession: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, session_id: int) -> None: ...
