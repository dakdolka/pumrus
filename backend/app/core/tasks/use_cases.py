from typing import List, Any, Optional

from app.core.db import async_session_factory
from app.core.theory.enums import TheorySubject

from .entities import Task, TaskItem
from .enums import TrainerType, InputMode
from .repository import ITaskRepository
from .parsers import parse_raw_content


class CreateTaskUseCase:
    def __init__(self, repo: ITaskRepository):
        self.repo = repo

    async def execute(
        self,
        name: str,
        subject: TheorySubject,
        trainer_type: TrainerType,
        input_mode: InputMode,
    ) -> Task:
        task = Task(
            id=None,
            name=name,
            subj=subject,
            trainer_type=trainer_type,
            input_mode=input_mode,
            is_active=True,
            items=[],
        )
        async with async_session_factory() as session:
            created = await self.repo.create_task(session, task)
        return created


class UpdateTaskUseCase:
    def __init__(self, repo: ITaskRepository):
        self.repo = repo

    async def execute(
        self,
        task_id: int,
        name: Optional[str] = None,
        trainer_type: Optional[TrainerType] = None,
        input_mode: Optional[InputMode] = None,
        is_active: Optional[bool] = None,
    ) -> Task:
        async with async_session_factory() as session:
            task = await self.repo.get_task_by_id(session, task_id)
            if not task:
                raise ValueError("Task not found")

            if name is not None:
                task.name = name
            if trainer_type is not None:
                task.trainer_type = trainer_type
            if input_mode is not None:
                task.input_mode = input_mode
            if is_active is not None:
                task.is_active = is_active

            updated = await self.repo.update_task(session, task)
        return updated


class GetTaskByIdUseCase:
    def __init__(self, repo: ITaskRepository):
        self.repo = repo

    async def execute(self, task_id: int) -> Optional[Task]:
        async with async_session_factory() as session:
            return await self.repo.get_task_by_id(session, task_id)


class GetTasksForSubjectUseCase:
    def __init__(self, repo: ITaskRepository):
        self.repo = repo

    async def execute(self, subject_id: int) -> List[Task]:
        async with async_session_factory() as session:
            return await self.repo.get_tasks_for_subject(session, subject_id)


class ReplaceTaskItemsUseCase:
    def __init__(self, repo: ITaskRepository):
        self.repo = repo

    async def execute(self, task_id: int, items: List[TaskItem]) -> None:
        async with async_session_factory() as session:
            await self.repo.replace_task_items(session, task_id, items)


class ParseRawContentUseCase:
    """
    Для формы: принимает raw-массив, тип тренажёра и (опц.) task_id,
    возвращает нормализованные TaskItem без сохранения.
    """

    def __init__(self):
        # репозиторий тут не нужен, только доменная логика парсинга
        ...

    async def execute(
        self,
        trainer_type: TrainerType,
        raw_content: Any,
        task_id: int = 0,
    ) -> List[TaskItem]:
        # task_id здесь может быть 0/None, нужен только чтобы проставить в сущности
        return parse_raw_content(task_id, trainer_type, raw_content)
