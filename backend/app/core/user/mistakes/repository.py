from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import UserMistake


class IUserMistakesRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession,
                        mistake_id: int) -> Optional[UserMistake]: ...

    @abstractmethod
    async def get_all_by_user(self, session: AsyncSession,
                               user_id: int) -> List[UserMistake]: ...

    @abstractmethod
    async def get_unresolved_by_user(self, session: AsyncSession,
                                     user_id: int) -> List[UserMistake]: ...

    @abstractmethod
    async def get_by_session(self, session: AsyncSession,
                             task_session_id: int) -> List[UserMistake]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, user_id: int, task_session_id: int,
                     mistake_item_id: int, chosen_option_id: int) -> UserMistake: ...

    @abstractmethod
    async def resolve(self, session: AsyncSession,
                      mistake_id: int) -> UserMistake: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, mistake_id: int) -> None: ...
