from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import Task, TaskItem, Option, OptionSet, TaskGroup
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
    def __init__(self, repo: ITaskGroupRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self) -> List[TaskGroup]:
        return await self.repo.get_all(self.session)


class GetTaskGroupByIdUseCase:
    def __init__(self, repo: ITaskGroupRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, group_id: int) -> TaskGroup:
        group = await self.repo.get_by_id(self.session, group_id)
        if not group:
            raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
        return group


class CreateTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, name: str) -> TaskGroup:
        async with self.session.begin():
            return await self.repo.create(self.session, name)


class UpdateTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, group_id: int, name: str) -> TaskGroup:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, group_id):
                raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
            return await self.repo.update(self.session, group_id, name)


class DeleteTaskGroupUseCase:
    def __init__(self, repo: ITaskGroupRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, group_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, group_id):
                raise TaskGroupNotFoundError(f"TaskGroup {group_id} не найден")
            await self.repo.delete(self.session, group_id)


# ── Option ────────────────────────────────────────────────────────────────────

class ListOptionsUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self) -> List[Option]:
        return await self.repo.get_all(self.session)


class GetOptionByContentUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, content: str) -> Optional[Option]:
        return await self.repo.get_by_content(self.session, content)


class GetOrCreateOptionUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, content: str,
                      extras: Optional[str]) -> tuple[Option, bool]:
        async with self.session.begin():
            existing = await self.repo.get_by_content(self.session, content)
            if existing:
                return existing, False
            option = await self.repo.create(self.session, content, extras)
            return option, True


class CreateOptionUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, content: str, extras: Optional[str]) -> Option:
        async with self.session.begin():
            return await self.repo.create(self.session, content, extras)


class UpdateOptionUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, option_id: int, content: Optional[str],
                      extras: Optional[str]) -> Option:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, option_id):
                raise OptionNotFoundError(f"Option {option_id} не найдена")
            return await self.repo.update(self.session, option_id, content, extras)


class DeleteOptionUseCase:
    def __init__(self, repo: IOptionRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, option_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, option_id):
                raise OptionNotFoundError(f"Option {option_id} не найдена")
            await self.repo.delete(self.session, option_id)


# ── OptionSet ─────────────────────────────────────────────────────────────────

class ListOptionSetsUseCase:
    def __init__(self, repo: IOptionSetRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self) -> List[OptionSet]:
        return await self.repo.get_all(self.session)


class GetOptionSetByIdUseCase:
    def __init__(self, repo: IOptionSetRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, set_id: int) -> OptionSet:
        result = await self.repo.get_by_id(self.session, set_id)
        if not result:
            raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
        return result


class CreateOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, name: str, option_ids: List[int]) -> OptionSet:
        async with self.session.begin():
            return await self.repo.create(self.session, name, option_ids)


class UpdateOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, set_id: int, name: Optional[str],
                      option_ids: Optional[List[int]]) -> OptionSet:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, set_id):
                raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
            return await self.repo.update(self.session, set_id, name, option_ids)


class DeleteOptionSetUseCase:
    def __init__(self, repo: IOptionSetRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, set_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, set_id):
                raise OptionSetNotFoundError(f"OptionSet {set_id} не найден")
            await self.repo.delete(self.session, set_id)


# ── Task ──────────────────────────────────────────────────────────────────────

class ListTasksUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self) -> List[Task]:
        return await self.repo.get_all(self.session)


class ListTasksByGroupUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, group_id: int) -> List[Task]:
        return await self.repo.get_all_by_group(self.session, group_id)


class GetTaskByIdUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, task_id: int) -> Task:
        task = await self.repo.get_by_id(self.session, task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} не найден")
        return task


class CreateTaskUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, name: str, group_id: int,
                      default_option_set_id: Optional[int]) -> Task:
        async with self.session.begin():
            return await self.repo.create(
                self.session, name, group_id, default_option_set_id
            )


class UpdateTaskUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, task_id: int, name: Optional[str],
                      group_id: Optional[int],
                      default_option_set_id: Optional[int]) -> Task:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, task_id):
                raise TaskNotFoundError(f"Task {task_id} не найден")
            return await self.repo.update(
                self.session, task_id, name, group_id, default_option_set_id
            )


class DeleteTaskUseCase:
    def __init__(self, repo: ITaskRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, task_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, task_id):
                raise TaskNotFoundError(f"Task {task_id} не найден")
            await self.repo.delete(self.session, task_id)


# ── TaskItem ──────────────────────────────────────────────────────────────────

class CreateTaskItemUseCase:
    def __init__(self, task_repo: ITaskRepository,
                 item_repo: ITaskItemRepository, session: AsyncSession):
        self.task_repo = task_repo; self.item_repo = item_repo; self.session = session

    async def execute(self, task_id: int, content_raw: str, content_visible: str,
                      content_correct: str, correct_option_id: Optional[int],
                      option_set_override_id: Optional[int],
                      notice_wrong: Optional[str],
                      notice_right: Optional[str]) -> TaskItem:
        async with self.session.begin():
            if not await self.task_repo.get_by_id(self.session, task_id):
                raise TaskNotFoundError(f"Task {task_id} не найден")
            return await self.item_repo.create(
                self.session, task_id, content_raw, content_visible, content_correct,
                correct_option_id, option_set_override_id, notice_wrong, notice_right,
            )


class CreateTaskItemsBulkUseCase:
    def __init__(self, task_repo: ITaskRepository,
                 item_repo: ITaskItemRepository, session: AsyncSession):
        self.task_repo = task_repo; self.item_repo = item_repo; self.session = session

    async def execute(self, task_id: int, items: list) -> List[TaskItem]:
        async with self.session.begin():
            if not await self.task_repo.get_by_id(self.session, task_id):
                raise TaskNotFoundError(f"Task {task_id} не найден")
            result = []
            for item in items:
                result.append(await self.item_repo.create(
                    self.session, task_id,
                    item.content_raw, item.content_visible, item.content_correct,
                    item.correct_option_id, item.option_set_override_id,
                    item.notice_wrong, item.notice_right,
                ))
            return result


class UpdateTaskItemUseCase:
    def __init__(self, repo: ITaskItemRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, item_id: int, content_raw: Optional[str],
                      content_visible: Optional[str], content_correct: Optional[str],
                      correct_option_id: Optional[int],
                      option_set_override_id: Optional[int],
                      notice_wrong: Optional[str],
                      notice_right: Optional[str]) -> TaskItem:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, item_id):
                raise TaskItemNotFoundError(f"TaskItem {item_id} не найден")
            return await self.repo.update(
                self.session, item_id, content_raw, content_visible, content_correct,
                correct_option_id, option_set_override_id, notice_wrong, notice_right,
            )


class UpdateTaskItemsBulkUseCase:
    def __init__(self, repo: ITaskItemRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, items: list) -> List[TaskItem]:
        async with self.session.begin():
            result = []
            for item in items:
                if not await self.repo.get_by_id(self.session, item.id):
                    raise TaskItemNotFoundError(f"TaskItem {item.id} не найден")
                result.append(await self.repo.update(
                    self.session, item.id,
                    item.content_raw, item.content_visible, item.content_correct,
                    item.correct_option_id, item.option_set_override_id,
                    item.notice_wrong, item.notice_right,
                ))
            return result


class DeleteTaskItemUseCase:
    def __init__(self, repo: ITaskItemRepository, session: AsyncSession):
        self.repo = repo; self.session = session

    async def execute(self, item_id: int) -> None:
        async with self.session.begin():
            if not await self.repo.get_by_id(self.session, item_id):
                raise TaskItemNotFoundError(f"TaskItem {item_id} не найден")
            await self.repo.delete(self.session, item_id)
