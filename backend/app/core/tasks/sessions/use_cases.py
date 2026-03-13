from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tasks.general.exceptions import TaskNotFoundError
from app.core.tasks.general.repository import ITaskRepository
from .entities import TaskSession
from .exceptions import TaskSessionNotFoundError
from .repository import ITaskSessionRepository


class InitiateTaskSessionUseCase:
    def __init__(self, session_repo: ITaskSessionRepository,
                 task_repo: ITaskRepository, session: AsyncSession):
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.session = session

    async def execute(self, user_id: int, task_id: int) -> TaskSession:
        async with self.session.begin():
            task = await self.task_repo.get_by_id(self.session, task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} не найден")
            existing = await self.session_repo.get_by_user_and_task(
                self.session, user_id, task_id
            )
            if existing and existing.is_open:
                existing.task = task
                return existing
            new_session = await self.session_repo.create(self.session, user_id, task_id)
            new_session.task = task
            return new_session


class CloseTaskSessionUseCase:
    def __init__(self, repo: ITaskSessionRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, session_id: int) -> TaskSession:
        async with self.session.begin():
            task_session = await self.repo.get_by_id(self.session, session_id)
            if not task_session:
                raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
            if not task_session.is_open:
                return task_session
            return await self.repo.close(
                self.session, session_id, datetime.now(timezone.utc)
            )


class GetTaskSessionUseCase:
    def __init__(self, session_repo: ITaskSessionRepository,
                 task_repo: ITaskRepository, session: AsyncSession):
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.session = session

    async def execute(self, session_id: int) -> TaskSession:
        result = await self.session_repo.get_by_id(self.session, session_id)
        if not result:
            raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
        result.task = await self.task_repo.get_by_id(self.session, result.task_id)
        return result


class GetUserSessionsUseCase:
    def __init__(self, session_repo: ITaskSessionRepository,
                 task_repo: ITaskRepository, session: AsyncSession):
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.session = session

    async def execute(self, user_id: int) -> List[TaskSession]:
        sessions = await self.session_repo.get_all_by_user(self.session, user_id)
        for s in sessions:
            s.task = await self.task_repo.get_by_id(self.session, s.task_id)
        return sessions


class DeleteTaskSessionUseCase:
    def __init__(self, repo: ITaskSessionRepository, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def execute(self, session_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, session_id):
                raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
            await self.repo.delete(self.session, session_id)
