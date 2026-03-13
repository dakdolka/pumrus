from fastapi import APIRouter, HTTPException
from typing import List
from app.core.tasks.sessions.use_cases import (
    InitiateTaskSessionUseCase, CloseTaskSessionUseCase,
    GetTaskSessionUseCase, GetUserSessionsUseCase, DeleteTaskSessionUseCase,
)
from app.core.tasks.sessions.exceptions import TaskSessionNotFoundError
from app.core.tasks.general.exceptions import TaskNotFoundError
from app.infra.tasks.sessions.repository_impl import TaskSessionRepositoryImpl
from app.infra.tasks.general.repository_impl import TaskRepositoryImpl
from .schemas import TaskSessionInitIn, TaskSessionOut

router = APIRouter(prefix="/tasks/sessions", tags=["task-sessions"])


@router.post("/initiate", response_model=TaskSessionOut, status_code=201)
async def initiate_session(body: TaskSessionInitIn):
    """Вход пользователя в задание."""
    try:
        return await InitiateTaskSessionUseCase(
            TaskSessionRepositoryImpl(), TaskRepositoryImpl()
        ).execute(body.user_id, body.task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/{session_id}/close", response_model=TaskSessionOut)
async def close_session(session_id: int):
    """Выход из задания."""
    try:
        return await CloseTaskSessionUseCase(TaskSessionRepositoryImpl()).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/{session_id}", response_model=TaskSessionOut)
async def get_session(session_id: int):
    try:
        return await GetTaskSessionUseCase(
            TaskSessionRepositoryImpl(), TaskRepositoryImpl()
        ).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/by-user/{user_id}", response_model=List[TaskSessionOut])
async def get_user_sessions(user_id: int):
    return await GetUserSessionsUseCase(
        TaskSessionRepositoryImpl(), TaskRepositoryImpl()
    ).execute(user_id)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: int):
    try:
        await DeleteTaskSessionUseCase(TaskSessionRepositoryImpl()).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))
