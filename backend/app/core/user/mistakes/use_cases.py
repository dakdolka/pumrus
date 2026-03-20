from os import strerror
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import UserMistake
from .exceptions import UserMistakeNotFoundError
from .repository import IUserMistakesRepository


class CreateUserMistakeUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int, task_session_id: int,
                      mistake_item_id: int, chosen_option_id: int, chosen_option_override: str) -> UserMistake:
        async with self.session.begin():
            return await self.repo.create(
                self.session, user_id, task_session_id,
                mistake_item_id, chosen_option_id, chosen_option_override
            )


class GetUserMistakesUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> List[UserMistake]:
        return await self.repo.get_all_by_user(self.session, user_id)


class GetUnresolvedMistakesUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, user_id: int) -> List[UserMistake]:
        return await self.repo.get_unresolved_by_user(self.session, user_id)


class GetMistakesBySessionUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, task_session_id: int) -> List[UserMistake]:
        return await self.repo.get_by_session(self.session, task_session_id)


class ResolveMistakeUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, mistake_id: int) -> UserMistake:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, mistake_id):
                raise UserMistakeNotFoundError(f"UserMistake {mistake_id} не найдена")
            return await self.repo.resolve(self.session, mistake_id)


class DeleteUserMistakeUseCase:
    def __init__(self, repo: IUserMistakesRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, mistake_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, mistake_id):
                raise UserMistakeNotFoundError(f"UserMistake {mistake_id} не найдена")
            await self.repo.delete(self.session, mistake_id)
