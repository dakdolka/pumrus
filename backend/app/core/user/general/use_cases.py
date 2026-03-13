from datetime import datetime, timezone
from typing import List, Optional
from app.core.db import async_session_factory
from .entities import User
from .exceptions import UserNotFoundError, UserAlreadyExistsError
from .repository import IUserRepository


class GetOrCreateUserUseCase:
    """Вызывается при старте бота — находит юзера по tg_id или регистрирует."""
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, tg_id: str, name: str,
                      second_name: Optional[str] = None,
                      username: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> tuple[User, bool]:
        async with async_session_factory() as db:
            async with db.begin():
                existing = await self.repo.get_by_tg_id(db, tg_id)
                if existing:
                    return existing, False
                user = await self.repo.create(db, tg_id, name, second_name,
                                              username, avatar_url)
                return user, True


class GetUserByIdUseCase:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> User:
        async with async_session_factory() as db:
            user = await self.repo.get_by_id(db, user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} не найден")
            return user


class GetUserByTgIdUseCase:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, tg_id: str) -> User:
        async with async_session_factory() as db:
            user = await self.repo.get_by_tg_id(db, tg_id)
            if not user:
                raise UserNotFoundError(f"User с tg_id={tg_id} не найден")
            return user


class ListUsersUseCase:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self) -> List[User]:
        async with async_session_factory() as db:
            return await self.repo.get_all(db)


class UpdateUserUseCase:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: int, name: Optional[str] = None,
                      second_name: Optional[str] = None,
                      username: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> User:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, user_id):
                    raise UserNotFoundError(f"User {user_id} не найден")
                return await self.repo.update(db, user_id, name, second_name,
                                              username, avatar_url)


class DeactivateUserUseCase:
    """Мягкий бан."""
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> User:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, user_id):
                    raise UserNotFoundError(f"User {user_id} не найден")
                return await self.repo.set_active(db, user_id, False)


class ActivateUserUseCase:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> User:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, user_id):
                    raise UserNotFoundError(f"User {user_id} не найден")
                return await self.repo.set_active(db, user_id, True)


class TouchLastActiveUseCase:
    """Вызывается автоматически при initiate_session."""
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> None:
        async with async_session_factory() as db:
            async with db.begin():
                await self.repo.touch_last_active(db, user_id, datetime.now(timezone.utc))
