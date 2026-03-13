from app.core.user.general.entities import User
from app.infra.user.general import UserBD


def map_user(m: UserBD) -> User:
    return User(
        id=m.id,
        tg_id=m.tg_id,
        name=m.name,
        second_name=m.second_name,
        username=m.username,
        avatar_url=m.avatar_url,
        birth_date=m.birth_date,
        is_active=m.is_active,
        is_admin=m.is_admin,
        last_active_at=m.last_active_at,
        created_at=m.created_at,
    )
