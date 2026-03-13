from datetime import datetime, timezone
from typing import List
from app.core.db import async_session_factory
from app.core.tasks.general.exceptions import TaskNotFoundError
from app.core.tasks.general.repository import ITaskRepository
from .entities import TaskSession
from .exceptions import TaskSessionNotFoundError
from .repository import ITaskSessionRepository


class InitiateTaskSessionUseCase:
    """Вход пользователя в задание. Возвращает открытую сессию или создаёт новую."""
    def __init__(self, session_repo: ITaskSessionRepository, task_repo: ITaskRepository):
        self.session_repo = session_repo
        self.task_repo = task_repo

    async def execute(self, user_id: int, task_id: int) -> TaskSession:
        async with async_session_factory() as db:
            async with db.begin():
                task = await self.task_repo.get_by_id(db, task_id)
                if not task:
                    raise TaskNotFoundError(f"Task {task_id} не найден")
                existing = await self.session_repo.get_by_user_and_task(db, user_id, task_id)
                if existing and existing.is_open:
                    existing.task = task
                    return existing
                new_session = await self.session_repo.create(db, user_id, task_id)
                new_session.task = task
                return new_session


class CloseTaskSessionUseCase:
    """Выход пользователя из задания."""
    def __init__(self, repo: ITaskSessionRepository):
        self.repo = repo

    async def execute(self, session_id: int) -> TaskSession:
        async with async_session_factory() as db:
            async with db.begin():
                task_session = await self.repo.get_by_id(db, session_id)
                if not task_session:
                    raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
                if not task_session.is_open:
                    return task_session  # идемпотентно
                return await self.repo.close(db, session_id, datetime.now(timezone.utc))


class GetTaskSessionUseCase:
    def __init__(self, session_repo: ITaskSessionRepository, task_repo: ITaskRepository):
        self.session_repo = session_repo
        self.task_repo = task_repo

    async def execute(self, session_id: int) -> TaskSession:
        async with async_session_factory() as db:
            result = await self.session_repo.get_by_id(db, session_id)
            if not result:
                raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
            result.task = await self.task_repo.get_by_id(db, result.task_id)
            return result


class GetUserSessionsUseCase:
    def __init__(self, session_repo: ITaskSessionRepository, task_repo: ITaskRepository):
        self.session_repo = session_repo
        self.task_repo = task_repo

    async def execute(self, user_id: int) -> List[TaskSession]:
        async with async_session_factory() as db:
            sessions = await self.session_repo.get_all_by_user(db, user_id)
            for s in sessions:
                s.task = await self.task_repo.get_by_id(db, s.task_id)
            return sessions


class DeleteTaskSessionUseCase:
    def __init__(self, repo: ITaskSessionRepository):
        self.repo = repo

    async def execute(self, session_id: int) -> None:
        async with async_session_factory() as db:
            async with db.begin():
                if not await self.repo.get_by_id(db, session_id):
                    raise TaskSessionNotFoundError(f"TaskSession {session_id} не найдена")
                await self.repo.delete(db, session_id)
