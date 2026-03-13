from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.db import get_db
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
async def initiate_session(body: TaskSessionInitIn,
                           db: AsyncSession = Depends(get_db)):
    try:
        return await InitiateTaskSessionUseCase(
            TaskSessionRepositoryImpl(), TaskRepositoryImpl(), db
        ).execute(body.user_id, body.task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/{session_id}/close", response_model=TaskSessionOut)
async def close_session(session_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await CloseTaskSessionUseCase(
            TaskSessionRepositoryImpl(), db
        ).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/{session_id}", response_model=TaskSessionOut)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await GetTaskSessionUseCase(
            TaskSessionRepositoryImpl(), TaskRepositoryImpl(), db
        ).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/by-user/{user_id}", response_model=List[TaskSessionOut])
async def get_user_sessions(user_id: int, db: AsyncSession = Depends(get_db)):
    return await GetUserSessionsUseCase(
        TaskSessionRepositoryImpl(), TaskRepositoryImpl(), db
    ).execute(user_id)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteTaskSessionUseCase(TaskSessionRepositoryImpl(), db).execute(session_id)
    except TaskSessionNotFoundError as e:
        raise HTTPException(404, detail=str(e))
