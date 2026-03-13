from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.user.general.entities import User
from app.core.user.general.repository import IUserRepository
from app.infra.user.general import UserBD
from . import mappers


class UserRepositoryImpl(IUserRepository):

    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(UserBD).where(UserBD.id == user_id))
        m = result.scalars().one_or_none()
        return mappers.map_user(m) if m else None

    async def get_by_tg_id(self, session: AsyncSession, tg_id: str) -> Optional[User]:
        result = await session.execute(select(UserBD).where(UserBD.tg_id == tg_id))
        m = result.scalars().one_or_none()
        return mappers.map_user(m) if m else None

    async def get_all(self, session: AsyncSession) -> List[User]:
        result = await session.execute(select(UserBD).order_by(UserBD.id))
        return [mappers.map_user(m) for m in result.scalars().all()]

    async def create(self, session: AsyncSession, tg_id: str, name: str,
                     second_name: Optional[str], username: Optional[str],
                     avatar_url: Optional[str]) -> User:
        m = UserBD(tg_id=tg_id, name=name, second_name=second_name,
                   username=username, avatar_url=avatar_url)
        session.add(m)
        await session.flush()
        return mappers.map_user(m)

    async def update(self, session: AsyncSession, user_id: int, name: Optional[str],
                     second_name: Optional[str], username: Optional[str],
                     avatar_url: Optional[str]) -> User:
        result = await session.execute(select(UserBD).where(UserBD.id == user_id))
        m = result.scalars().one()
        if name is not None:         m.name = name
        if second_name is not None:  m.second_name = second_name
        if username is not None:     m.username = username
        if avatar_url is not None:   m.avatar_url = avatar_url
        await session.flush()
        return mappers.map_user(m)

    async def set_active(self, session: AsyncSession,
                         user_id: int, is_active: bool) -> User:
        result = await session.execute(select(UserBD).where(UserBD.id == user_id))
        m = result.scalars().one()
        m.is_active = is_active
        await session.flush()
        return mappers.map_user(m)

    async def touch_last_active(self, session: AsyncSession,
                                user_id: int, dt: datetime) -> None:
        result = await session.execute(select(UserBD).where(UserBD.id == user_id))
        m = result.scalars().one()
        m.last_active_at = dt
        await session.flush()
