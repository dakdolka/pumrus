from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import User


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]: ...

    @abstractmethod
    async def get_by_tg_id(self, session: AsyncSession, tg_id: str) -> Optional[User]: ...

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[User]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, tg_id: str, name: str,
                     second_name: Optional[str], username: Optional[str],
                     avatar_url: Optional[str]) -> User: ...

    @abstractmethod
    async def update(self, session: AsyncSession, user_id: int, name: Optional[str],
                     second_name: Optional[str], username: Optional[str],
                     avatar_url: Optional[str]) -> User: ...

    @abstractmethod
    async def set_active(self, session: AsyncSession,
                         user_id: int, is_active: bool) -> User: ...

    @abstractmethod
    async def touch_last_active(self, session: AsyncSession,
                                user_id: int, dt: datetime) -> None: ...
