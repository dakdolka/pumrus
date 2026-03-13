from app.core.tasks.sessions.entities import TaskSession
from app.infra.tasks.sessions.models import TaskSessionBD


def map_task_session(m: TaskSessionBD) -> TaskSession:
    return TaskSession(
        id=m.id,
        user_id=m.user_id,
        task_id=m.task_id,
        created_at=m.created_at,
        closed_at=m.closed_at,
    )
