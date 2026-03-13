from fastapi import APIRouter, HTTPException
from typing import List
from app.core.user.mistakes.use_cases import (
    CreateUserMistakeUseCase, GetUserMistakesUseCase,
    GetUnresolvedMistakesUseCase, GetMistakesBySessionUseCase,
    ResolveMistakeUseCase, DeleteUserMistakeUseCase,
)
from app.core.user.mistakes.exceptions import UserMistakeNotFoundError
from app.infra.user.mistakes.repository_impl import UserMistakesRepositoryImpl
from .schemas import UserMistakeCreateIn, UserMistakeOut

router = APIRouter(prefix="/users/mistakes", tags=["user-mistakes"])


@router.post("/", response_model=UserMistakeOut, status_code=201)
async def create_mistake(body: UserMistakeCreateIn):
    return await CreateUserMistakeUseCase(UserMistakesRepositoryImpl()).execute(
        body.user_id, body.task_session_id, body.mistake_item_id, body.chosen_option_id
    )


@router.get("/by-user/{user_id}", response_model=List[UserMistakeOut])
async def get_user_mistakes(user_id: int):
    return await GetUserMistakesUseCase(UserMistakesRepositoryImpl()).execute(user_id)


@router.get("/by-user/{user_id}/unresolved", response_model=List[UserMistakeOut])
async def get_unresolved_mistakes(user_id: int):
    """Для режима 'повтори ошибки'."""
    return await GetUnresolvedMistakesUseCase(UserMistakesRepositoryImpl()).execute(user_id)


@router.get("/by-session/{session_id}", response_model=List[UserMistakeOut])
async def get_mistakes_by_session(session_id: int):
    return await GetMistakesBySessionUseCase(UserMistakesRepositoryImpl()).execute(session_id)


@router.post("/{mistake_id}/resolve", response_model=UserMistakeOut)
async def resolve_mistake(mistake_id: int):
    try:
        return await ResolveMistakeUseCase(UserMistakesRepositoryImpl()).execute(mistake_id)
    except UserMistakeNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/{mistake_id}", status_code=204)
async def delete_mistake(mistake_id: int):
    try:
        await DeleteUserMistakeUseCase(UserMistakesRepositoryImpl()).execute(mistake_id)
    except UserMistakeNotFoundError as e:
        raise HTTPException(404, detail=str(e))
