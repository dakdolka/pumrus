from typing import List, Optional

from app.core.db import async_session_factory
from .entities import Task, TaskItem, OptionSet, Option, TaskGroup
from .repository import (
    ITaskRepository, ITaskItemRepository,
    IOptionSetRepository, IOptionRepository, ITaskGroupRepository,
)
from .exceptions import (
    TaskNotFoundError, TaskItemNotFoundError,
    OptionSetNotFoundError, OptionNotFoundError, TaskGroupNotFoundError,
)


# ── TaskGroup ─────────────────────────────────────────────────────────────────

class ListTaskGroupsUseCase:
    def __init__(self, repo: ITaskGroupRepository): self.repo = repo

    async def execute(self) -> List[TaskGroup]:
        async with async_session_factory() as session:
            return await self.repo.get_all(session)


class GetTaskGroupByIdUseCase:
    def __init__(self, repo: ITaskGroupRepository): self.repo = repo

    async def execute(self, group_id: int) -> TaskGroup:
        async with async_session_factory() as session:
            group = await self.repo.get_by_id(session, group_id)
            if not group:
                raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
            return group


class CreateTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository): self.repo = repo

    async def execute(self, name: str) -> TaskGroup:
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create(session, name)


class UpdateTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository): self.repo = repo

    async def execute(self, group_id: int, name: str) -> TaskGroup:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, group_id):
                    raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
                return await self.repo.update(session, group_id, name)


class DeleteTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository): self.repo = repo

    async def execute(self, group_id: int) -> None:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, group_id):
                    raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
                await self.repo.delete(session, group_id)


# ── Option ────────────────────────────────────────────────────────────────────

class ListOptionsUseCase:
    def __init__(self, repo: IOptionRepository): self.repo = repo

    async def execute(self) -> List[Option]:
        async with async_session_factory() as session:
            return await self.repo.get_all(session)


class CreateOptionUseCase:
    def __init__(self, repo: IOptionRepository): self.repo = repo

    async def execute(self, content: str, extras: Optional[str]) -> Option:
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create(session, content, extras)


class UpdateOptionUseCase:
    def __init__(self, repo: IOptionRepository): self.repo = repo

    async def execute(self, option_id: int, content: Optional[str],
                      extras: Optional[str]) -> Option:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, option_id):
                    raise OptionNotFoundError(f"Option {option_id} не найдена")
                return await self.repo.update(session, option_id, content, extras)


class DeleteOptionUseCase:
    def __init__(self, repo: IOptionRepository): self.repo = repo

    async def execute(self, option_id: int) -> None:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, option_id):
                    raise OptionNotFoundError(f"Option {option_id} не найдена")
                await self.repo.delete(session, option_id)


# ── OptionSet ─────────────────────────────────────────────────────────────────

class ListOptionSetsUseCase:
    def __init__(self, repo: IOptionSetRepository): self.repo = repo

    async def execute(self) -> List[OptionSet]:
        async with async_session_factory() as session:
            return await self.repo.get_all(session)


class GetOptionSetByIdUseCase:
    def __init__(self, repo: IOptionSetRepository): self.repo = repo

    async def execute(self, set_id: int) -> OptionSet:
        async with async_session_factory() as session:
            result = await self.repo.get_by_id(session, set_id)
            if not result:
                raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
            return result


class CreateOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository): self.repo = repo

    async def execute(self, name: str, option_ids: List[int]) -> OptionSet:
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create(session, name, option_ids)


class UpdateOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository): self.repo = repo

    async def execute(self, set_id: int, name: Optional[str],
                      option_ids: Optional[List[int]]) -> OptionSet:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, set_id):
                    raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
                return await self.repo.update(session, set_id, name, option_ids)


class DeleteOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository): self.repo = repo

    async def execute(self, set_id: int) -> None:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, set_id):
                    raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
                await self.repo.delete(session, set_id)


# ── Task ──────────────────────────────────────────────────────────────────────

class ListTasksUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self) -> List[Task]:
        async with async_session_factory() as session:
            return await self.repo.get_all(session)


class ListTasksByGroupUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self, group_id: int) -> List[Task]:
        async with async_session_factory() as session:
            return await self.repo.get_all_by_group(session, group_id)


class GetTaskByIdUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self, task_id: int) -> Task:
        async with async_session_factory() as session:
            task = await self.repo.get_by_id(session, task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} не найден")
            return task


class CreateTaskUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self, name: str, group_id: int,
                      default_option_set_id: Optional[int]) -> Task:
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create(session, name, group_id, default_option_set_id)


class UpdateTaskUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self, task_id: int, name: Optional[str],
                      group_id: Optional[int],
                      default_option_set_id: Optional[int]) -> Task:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, task_id):
                    raise TaskNotFoundError(f"Task {task_id} не найден")
                return await self.repo.update(
                    session, task_id, name, group_id, default_option_set_id
                )


class DeleteTaskUseCase:
    def __init__(self, repo: ITaskRepository): self.repo = repo

    async def execute(self, task_id: int) -> None:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, task_id):
                    raise TaskNotFoundError(f"Task {task_id} не найден")
                await self.repo.delete(session, task_id)


# ── TaskItem ──────────────────────────────────────────────────────────────────

class CreateTaskItemUseCase:
    def __init__(self, task_repo: ITaskRepository, item_repo: ITaskItemRepository):
        self.task_repo = task_repo
        self.item_repo = item_repo

    async def execute(self, task_id: int, content_raw: str, content_visible: str,
                      content_correct: str, correct_option_id: Optional[int],
                      option_set_override_id: Optional[int],
                      notice_wrong: Optional[str], notice_right: Optional[str]) -> TaskItem:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.task_repo.get_by_id(session, task_id):
                    raise TaskNotFoundError(f"Task {task_id} не найден")
                return await self.item_repo.create(
                    session, task_id, content_raw, content_visible, content_correct,
                    correct_option_id, option_set_override_id, notice_wrong, notice_right,
                )


class UpdateTaskItemUseCase:
    def __init__(self, repo: ITaskItemRepository): self.repo = repo

    async def execute(self, item_id: int, content_raw: Optional[str],
                      content_visible: Optional[str], content_correct: Optional[str],
                      correct_option_id: Optional[int], option_set_override_id: Optional[int],
                      notice_wrong: Optional[str], notice_right: Optional[str]) -> TaskItem:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, item_id):
                    raise TaskItemNotFoundError(f"TaskItem {item_id} не найден")
                return await self.repo.update(
                    session, item_id, content_raw, content_visible, content_correct,
                    correct_option_id, option_set_override_id, notice_wrong, notice_right,
                )


class DeleteTaskItemUseCase:
    def __init__(self, repo: ITaskItemRepository): self.repo = repo

    async def execute(self, item_id: int) -> None:
        async with async_session_factory() as session:
            async with session.begin():
                if not await self.repo.get_by_id(session, item_id):
                    raise TaskItemNotFoundError(f"TaskItem {item_id} не найден")
                await self.repo.delete(session, item_id)
