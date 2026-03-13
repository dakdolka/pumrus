from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import User
from .exceptions import UserNotFoundError
from .repository import IUserRepository
from datetime import datetime, timezone


class GetOrCreateUserUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, tg_id: str, name: str,
                      second_name: Optional[str] = None,
                      username: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> tuple[User, bool]:
        async with self.session.begin():
            existing = await self.repo.get_by_tg_id(self.session, tg_id)
            if existing:
                return existing, False
            user = await self.repo.create(self.session, tg_id, name,
                                          second_name, username, avatar_url)
            return user, True


class GetUserByIdUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> User:
        user = await self.repo.get_by_id(self.session, user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} не найден")
        return user


class GetUserByTgIdUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, tg_id: str) -> User:
        user = await self.repo.get_by_tg_id(self.session, tg_id)
        if not user:
            raise UserNotFoundError(f"User tg_id={tg_id} не найден")
        return user


class ListUsersUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self) -> List[User]:
        return await self.repo.get_all(self.session)


class UpdateUserUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int, name: Optional[str] = None,
                      second_name: Optional[str] = None,
                      username: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> User:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, user_id):
                raise UserNotFoundError(f"User {user_id} не найден")
            return await self.repo.update(self.session, user_id, name,
                                          second_name, username, avatar_url)


class DeactivateUserUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> User:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, user_id):
                raise UserNotFoundError(f"User {user_id} не найден")
            return await self.repo.set_active(self.session, user_id, False)


class ActivateUserUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> User:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, user_id):
                raise UserNotFoundError(f"User {user_id} не найден")
            return await self.repo.set_active(self.session, user_id, True)


class TouchLastActiveUseCase:
    def __init__(self, repo: IUserRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> None:
        async with self.session.begin():
            await self.repo.touch_last_active(
                self.session, user_id, datetime.now(timezone.utc)
            )
