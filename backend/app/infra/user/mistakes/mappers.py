from app.core.user.mistakes.entities import UserMistake
from app.infra.user.mistakes import UserMistakesBD
from app.infra.tasks.general.mappers import map_task_item, map_option


def map_user_mistake(m: UserMistakesBD) -> UserMistake:
    return UserMistake(
        id=m.id,
        user_id=m.user_fk,
        task_session_id=m.task_session_fk,
        mistake_item_id=m.mistake_item_fk,
        chosen_option_id=m.chosen_option_fk,
        is_resolved=m.is_resolved,
        mistake_item=map_task_item(m.mistake_item) if m.mistake_item else None,
        chosen_option=map_option(m.chosen_option) if m.chosen_option else None,
        created_at=m.created_at,
    )
