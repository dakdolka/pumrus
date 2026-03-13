from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tasks.general.entities import Task, TaskItem, Option, OptionSet, TaskGroup
from app.core.tasks.general.repository import (
    ITaskRepository, ITaskItemRepository,
    IOptionSetRepository, IOptionRepository, ITaskGroupRepository,
)
from .models import (
    TaskBD, TaskItemBD, OptionBD, OptionSetBD, TaskGroupBD,
)
from . import mappers


class TaskGroupRepositoryImpl(ITaskGroupRepository):

    async def get_all(self, session: AsyncSession) -> List[TaskGroup]:
        result = await session.execute(select(TaskGroupBD))
        return [mappers.map_task_group(g) for g in result.scalars().all()]

    async def get_by_id(self, session: AsyncSession, group_id: int) -> Optional[TaskGroup]:
        result = await session.execute(
            select(TaskGroupBD).where(TaskGroupBD.id == group_id)
        )
        m = result.scalars().one_or_none()
        return mappers.map_task_group(m) if m else None

    async def create(self, session: AsyncSession, name: str) -> TaskGroup:
        m = TaskGroupBD(name=name)
        session.add(m)
        await session.flush()
        return mappers.map_task_group(m)

    async def update(self, session: AsyncSession, group_id: int, name: str) -> TaskGroup:
        result = await session.execute(
            select(TaskGroupBD).where(TaskGroupBD.id == group_id)
        )
        m = result.scalars().one()
        m.name = name
        await session.flush()
        return mappers.map_task_group(m)

    async def delete(self, session: AsyncSession, group_id: int) -> None:
        await session.execute(delete(TaskGroupBD).where(TaskGroupBD.id == group_id))


class OptionRepositoryImpl(IOptionRepository):

    async def get_all(self, session: AsyncSession) -> List[Option]:
        result = await session.execute(select(OptionBD))
        return [mappers.map_option(o) for o in result.scalars().all()]

    async def get_by_id(self, session: AsyncSession, option_id: int) -> Optional[Option]:
        result = await session.execute(
            select(OptionBD).where(OptionBD.id == option_id)
        )
        m = result.scalars().one_or_none()
        return mappers.map_option(m) if m else None

    async def create(self, session: AsyncSession, content: str,
                     extras: Optional[str]) -> Option:
        m = OptionBD(content=content, extras=extras)
        session.add(m)
        await session.flush()
        return mappers.map_option(m)

    async def update(self, session: AsyncSession, option_id: int,
                     content: Optional[str], extras: Optional[str]) -> Option:
        result = await session.execute(
            select(OptionBD).where(OptionBD.id == option_id)
        )
        m = result.scalars().one()
        if content is not None:
            m.content = content
        if extras is not None:
            m.extras = extras
        await session.flush()
        return mappers.map_option(m)

    async def delete(self, session: AsyncSession, option_id: int) -> None:
        await session.execute(delete(OptionBD).where(OptionBD.id == option_id))


class OptionSetRepositoryImpl(IOptionSetRepository):

    _load = selectinload(OptionSetBD.options)

    async def get_all(self, session: AsyncSession) -> List[OptionSet]:
        result = await session.execute(select(OptionSetBD).options(self._load))
        return [mappers.map_option_set(s) for s in result.scalars().all()]

    async def get_by_id(self, session: AsyncSession, set_id: int) -> Optional[OptionSet]:
        result = await session.execute(
            select(OptionSetBD).where(OptionSetBD.id == set_id).options(self._load)
        )
        m = result.scalars().one_or_none()
        return mappers.map_option_set(m) if m else None

    async def create(self, session: AsyncSession, name: str,
                     option_ids: List[int]) -> OptionSet:
        options = (
            await session.execute(select(OptionBD).where(OptionBD.id.in_(option_ids)))
        ).scalars().all()
        m = OptionSetBD(name=name, options=list(options))
        session.add(m)
        await session.flush()
        await session.refresh(m, ["options"])
        return mappers.map_option_set(m)

    async def update(self, session: AsyncSession, set_id: int,
                     name: Optional[str], option_ids: Optional[List[int]]) -> OptionSet:
        result = await session.execute(
            select(OptionSetBD).where(OptionSetBD.id == set_id).options(self._load)
        )
        m = result.scalars().one()
        if name is not None:
            m.name = name
        if option_ids is not None:
            options = (
                await session.execute(select(OptionBD).where(OptionBD.id.in_(option_ids)))
            ).scalars().all()
            m.options = list(options)
        await session.flush()
        return mappers.map_option_set(m)

    async def delete(self, session: AsyncSession, set_id: int) -> None:
        await session.execute(delete(OptionSetBD).where(OptionSetBD.id == set_id))


class TaskRepositoryImpl(ITaskRepository):

    @staticmethod
    def _stmt():
        return (
            select(TaskBD)
            .options(
                selectinload(TaskBD.task_group),
                selectinload(TaskBD.default_option_set).selectinload(OptionSetBD.options),
                selectinload(TaskBD.items).selectinload(TaskItemBD.correct_option),
                selectinload(TaskBD.items)
                    .selectinload(TaskItemBD.option_set_override)
                    .selectinload(OptionSetBD.options),
            )
        )

    async def get_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        result = await session.execute(self._stmt().where(TaskBD.id == task_id))
        m = result.scalars().one_or_none()
        return mappers.map_task(m) if m else None

    async def get_all(self, session: AsyncSession) -> List[Task]:
        result = await session.execute(self._stmt())
        return [mappers.map_task(m) for m in result.scalars().all()]

    async def get_all_by_group(self, session: AsyncSession, group_id: int) -> List[Task]:
        result = await session.execute(
            self._stmt().where(TaskBD.task_group_fk == group_id)
        )
        return [mappers.map_task(m) for m in result.scalars().all()]

    async def create(self, session: AsyncSession, name: str, group_id: int,
                     default_option_set_id: Optional[int]) -> Task:
        m = TaskBD(name=name, task_group_fk=group_id,
                   default_option_set_fk=default_option_set_id)
        session.add(m)
        await session.flush()
        result = await session.execute(self._stmt().where(TaskBD.id == m.id))
        return mappers.map_task(result.scalars().one())

    async def update(self, session: AsyncSession, task_id: int, name: Optional[str],
                     group_id: Optional[int],
                     default_option_set_id: Optional[int]) -> Task:
        result = await session.execute(self._stmt().where(TaskBD.id == task_id))
        m = result.scalars().one()
        if name is not None:
            m.name = name
        if group_id is not None:
            m.task_group_fk = group_id
        if default_option_set_id is not None:
            m.default_option_set_fk = default_option_set_id
        await session.flush()
        result = await session.execute(self._stmt().where(TaskBD.id == task_id))
        return mappers.map_task(result.scalars().one())

    async def delete(self, session: AsyncSession, task_id: int) -> None:
        await session.execute(delete(TaskBD).where(TaskBD.id == task_id))


class TaskItemRepositoryImpl(ITaskItemRepository):

    @staticmethod
    def _stmt():
        return (
            select(TaskItemBD)
            .options(
                selectinload(TaskItemBD.correct_option),
                selectinload(TaskItemBD.option_set_override).selectinload(OptionSetBD.options),
            )
        )

    async def get_by_id(self, session: AsyncSession, item_id: int) -> Optional[TaskItem]:
        result = await session.execute(self._stmt().where(TaskItemBD.id == item_id))
        m = result.scalars().one_or_none()
        return mappers.map_task_item(m) if m else None

    async def create(self, session: AsyncSession, task_id: int, content_raw: str,
                     content_visible: str, content_correct: str,
                     correct_option_id: Optional[int], option_set_override_id: Optional[int],
                     notice_wrong: Optional[str], notice_right: Optional[str]) -> TaskItem:
        m = TaskItemBD(
            task_id=task_id,
            content_raw=content_raw,
            content_visible=content_visible,
            content_correct=content_correct,
            correct_option_fk=correct_option_id,
            option_set_override_fk=option_set_override_id,
            notice_wrong=notice_wrong,
            notice_right=notice_right,
        )
        session.add(m)
        await session.flush()
        result = await session.execute(self._stmt().where(TaskItemBD.id == m.id))
        return mappers.map_task_item(result.scalars().one())

    async def update(self, session: AsyncSession, item_id: int,
                     content_raw: Optional[str], content_visible: Optional[str],
                     content_correct: Optional[str], correct_option_id: Optional[int],
                     option_set_override_id: Optional[int],
                     notice_wrong: Optional[str], notice_right: Optional[str]) -> TaskItem:
        result = await session.execute(self._stmt().where(TaskItemBD.id == item_id))
        m = result.scalars().one()
        if content_raw is not None:        m.content_raw = content_raw
        if content_visible is not None:    m.content_visible = content_visible
        if content_correct is not None:    m.content_correct = content_correct
        if correct_option_id is not None:  m.correct_option_fk = correct_option_id
        if option_set_override_id is not None: m.option_set_override_fk = option_set_override_id
        if notice_wrong is not None:       m.notice_wrong = notice_wrong
        if notice_right is not None:       m.notice_right = notice_right
        await session.flush()
        result = await session.execute(self._stmt().where(TaskItemBD.id == item_id))
        return mappers.map_task_item(result.scalars().one())

    async def delete(self, session: AsyncSession, item_id: int) -> None:
        await session.execute(delete(TaskItemBD).where(TaskItemBD.id == item_id))
