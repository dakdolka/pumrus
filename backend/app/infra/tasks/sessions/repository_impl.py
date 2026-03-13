from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tasks.sessions.entities import TaskSession
from app.core.tasks.sessions.repository import ITaskSessionRepository
from app.infra.tasks.sessions.models import TaskSessionBD
from . import mappers


class TaskSessionRepositoryImpl(ITaskSessionRepository):

    async def get_by_id(self, session: AsyncSession, session_id: int) -> Optional[TaskSession]:
        result = await session.execute(
            select(TaskSessionBD).where(TaskSessionBD.id == session_id)
        )
        m = result.scalars().one_or_none()
        return mappers.map_task_session(m) if m else None

    async def get_by_user_and_task(self, session: AsyncSession,
                                   user_id: int, task_id: int) -> Optional[TaskSession]:
        result = await session.execute(
            select(TaskSessionBD)
            .where(TaskSessionBD.user_id == user_id, TaskSessionBD.task_id == task_id)
            .order_by(TaskSessionBD.created_at.desc())
        )
        m = result.scalars().first()
        return mappers.map_task_session(m) if m else None

    async def get_all_by_user(self, session: AsyncSession, user_id: int) -> List[TaskSession]:
        result = await session.execute(
            select(TaskSessionBD)
            .where(TaskSessionBD.user_id == user_id)
            .order_by(TaskSessionBD.created_at.desc())
        )
        return [mappers.map_task_session(m) for m in result.scalars().all()]

    async def create(self, session: AsyncSession,
                     user_id: int, task_id: int) -> TaskSession:
        m = TaskSessionBD(user_id=user_id, task_id=task_id)
        session.add(m)
        await session.flush()
        return mappers.map_task_session(m)

    async def close(self, session: AsyncSession,
                    session_id: int, closed_at: datetime) -> TaskSession:
        result = await session.execute(
            select(TaskSessionBD).where(TaskSessionBD.id == session_id)
        )
        m = result.scalars().one()
        m.closed_at = closed_at
        await session.flush()
        return mappers.map_task_session(m)

    async def delete(self, session: AsyncSession, session_id: int) -> None:
        await session.execute(delete(TaskSessionBD).where(TaskSessionBD.id == session_id))
