from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.theory.enums import TheorySubject
from app.core.tasks.entities import Task, TaskItem
from app.core.tasks.enums import TrainerType, InputMode
from app.core.tasks.repository import ITaskRepository

from .models import TaskBD, TaskItemBD


def _bd_to_domain_task(bd: TaskBD) -> Task:

    items = [
        TaskItem(
            id=item.id,
            task_id=bd.id,
            order=item.item_order,
            trainer_type=TrainerType(item.trainer_type),
            raw=item.raw,
            visible=item.visible,
            correct_option=item.correct_option,
            correct_visible=item.correct_visible,
            extra=item.extra_json or {},
        )
        for item in bd.items
    ]

    return Task(
        id=bd.id,
        name=bd.name,
        subj=TheorySubject(bd.subject_id),  # если используешь Enum с id, или маппинг иначе
        trainer_type=TrainerType(bd.trainer_type),
        input_mode=InputMode(bd.input_mode),
        is_active=bd.is_active,
        items=items,
    )


class TaskRepositoryImpl(ITaskRepository):
    async def create_task(self, session: AsyncSession, task: Task) -> Task:
        bd = TaskBD(
            name=task.name,
            subject_id=task.subj.value if hasattr(task.subj, "value") else task.subj,
            trainer_type=task.trainer_type.value,
            input_mode=task.input_mode.value,
            is_active=task.is_active,
        )
        session.add(bd)
        await session.flush()
        task.id = bd.id
        return task

    async def update_task(self, session: AsyncSession, task: Task) -> Task:
        q = await session.get(TaskBD, task.id)
        if not q:
            raise ValueError("Task not found")

        q.name = task.name
        q.subject_id = task.subj.value if hasattr(task.subj, "value") else task.subj
        q.trainer_type = task.trainer_type.value
        q.input_mode = task.input_mode.value
        q.is_active = task.is_active

        await session.flush()
        return task

    async def get_task_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        stmt = (
            select(TaskBD)
            .where(TaskBD.id == task_id)
            .options(TaskBD.items)  # при необходимости добавить selectinload
        )
        res = await session.execute(stmt)
        bd = res.scalars().one_or_none()
        if not bd:
            return None
        return _bd_to_domain_task(bd)

    async def get_tasks_for_subject(
        self, session: AsyncSession, subject_id: int
    ) -> List[Task]:
        stmt = select(TaskBD).where(TaskBD.subject_id == subject_id)
        res = await session.execute(stmt)
        bds = res.scalars().all()
        return [_bd_to_domain_task(bd) for bd in bds]

    async def replace_task_items(
        self, session: AsyncSession, task_id: int, items: List[TaskItem]
    ) -> None:
        # удалить старые
        await session.execute(
            delete(TaskItemBD).where(TaskItemBD.task_id == task_id)
        )
        # добавить новые
        for it in items:
            bd_item = TaskItemBD(
                task_id=task_id,
                item_order=it.order,
                trainer_type=it.trainer_type.value,
                raw=it.raw,
                visible=it.visible,
                correct_option=it.correct_option,
                correct_visible=it.correct_visible,
                extra_json=it.extra or {},
            )
            session.add(bd_item)
        await session.flush()
