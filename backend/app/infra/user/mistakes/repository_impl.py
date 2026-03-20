from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.user.mistakes.entities import UserMistake
from app.core.user.mistakes.repository import IUserMistakesRepository
from app.infra.user.mistakes import UserMistakesBD
from . import mappers
from app.infra.tasks.general import TaskItemBD
from app.infra.tasks.general import OptionSetBD



class UserMistakesRepositoryImpl(IUserMistakesRepository):

    @staticmethod
    def _stmt():
        return (
            select(UserMistakesBD)
            .options(
                selectinload(UserMistakesBD.chosen_option),
                selectinload(UserMistakesBD.mistake_item).options(
                    selectinload(TaskItemBD.correct_option),
                    selectinload(TaskItemBD.option_set_override).selectinload(OptionSetBD.options),
                ),
            )
        )

    async def get_by_id(self, session: AsyncSession,
                        mistake_id: int) -> Optional[UserMistake]:
        result = await session.execute(
            self._stmt().where(UserMistakesBD.id == mistake_id)
        )
        m = result.scalars().one_or_none()
        return mappers.map_user_mistake(m) if m else None

    async def get_all_by_user(self, session: AsyncSession,
                               user_id: int) -> List[UserMistake]:
        result = await session.execute(
            self._stmt()
            .where(UserMistakesBD.user_fk == user_id)
            .order_by(UserMistakesBD.created_at.desc())
        )
        return [mappers.map_user_mistake(m) for m in result.scalars().all()]

    async def get_unresolved_by_user(self, session: AsyncSession,
                                     user_id: int) -> List[UserMistake]:
        result = await session.execute(
            self._stmt()
            .where(UserMistakesBD.user_fk == user_id,
                   UserMistakesBD.is_resolved == False)
            .order_by(UserMistakesBD.created_at.desc())
        )
        return [mappers.map_user_mistake(m) for m in result.scalars().all()]

    async def get_by_session(self, session: AsyncSession,
                             task_session_id: int) -> List[UserMistake]:
        result = await session.execute(
            self._stmt().where(UserMistakesBD.task_session_fk == task_session_id)
        )
        return [mappers.map_user_mistake(m) for m in result.scalars().all()]

    async def create(self, session: AsyncSession, user_id: int, task_session_id: int,
                    mistake_item_id: int, chosen_option_id: int, chosen_option_override: str) -> UserMistake:
        # Проверка на нерезолвнутый дубль
        existing = await session.execute(
            self._stmt().where(
                UserMistakesBD.user_fk         == user_id,
                UserMistakesBD.mistake_item_fk == mistake_item_id,
                UserMistakesBD.is_resolved     == False,
            )
        )
        found = existing.scalars().first()
        if found:
            return mappers.map_user_mistake(found)

        # Создаём новую
        m = UserMistakesBD(
            user_fk=user_id,
            task_session_fk=task_session_id,
            mistake_item_fk=mistake_item_id,
            chosen_option_fk=chosen_option_id,
            chosen_option_override=chosen_option_override,
        )
        session.add(m)
        await session.flush()
        result = await session.execute(self._stmt().where(UserMistakesBD.id == m.id))
        return mappers.map_user_mistake(result.scalars().one())


    async def resolve(self, session: AsyncSession, mistake_id: int) -> UserMistake:
        result = await session.execute(
            self._stmt().where(UserMistakesBD.id == mistake_id)
        )
        m = result.scalars().one()
        m.is_resolved = True
        await session.flush()
        await session.refresh(m)
        return mappers.map_user_mistake(m)

    async def delete(self, session: AsyncSession, mistake_id: int) -> None:
        await session.execute(
            delete(UserMistakesBD).where(UserMistakesBD.id == mistake_id)
        )
