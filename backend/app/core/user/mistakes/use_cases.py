from typing import List
from app.core.db import async_session_factory
from .entities import UserMistake
from .exceptions import UserMistakeNotFoundError
from .repository import IUserMistakesRepository


class CreateUserMistakeUseCase:
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, user_id: int, task_session_id: int,
                      mistake_item_id: int, chosen_option_id: int) -> UserMistake:
        async with async_session_factory() as db:
            async with db.begin():
                return await self.repo.create(
                    db, user_id, task_session_id, mistake_item_id, chosen_option_id
                )


class GetUserMistakesUseCase:
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> List[UserMistake]:
        async with async_session_factory() as db:
            return await self.repo.get_all_by_user(db, user_id)


class GetUnresolvedMistakesUseCase:
    """Для режима 'повтори ошибки'."""
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> List[UserMistake]:
        async with async_session_factory() as db:
            return await self.repo.get_unresolved_by_user(db, user_id)


class GetMistakesBySessionUseCase:
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, task_session_id: int) -> List[UserMistake]:
        async with async_session_factory() as db:
            return await self.repo.get_by_session(db, task_session_id)


class ResolveMistakeUseCase:
    """Пользователь исправил ошибку."""
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, mistake_id: int) -> UserMistake:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, mistake_id):
                    raise UserMistakeNotFoundError(f"UserMistake {mistake_id} не найдена")
                return await self.repo.resolve(db, mistake_id)


class DeleteUserMistakeUseCase:
    def __init__(self, repo: IUserMistakesRepository):
        self.repo = repo

    async def execute(self, mistake_id: int) -> None:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, mistake_id):
                    raise UserMistakeNotFoundError(f"UserMistake {mistake_id} не найдена")
                await self.repo.delete(db, mistake_id)
