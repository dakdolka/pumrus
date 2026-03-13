from fastapi import APIRouter, HTTPException
from typing import List
from app.core.user.general.use_cases import (
    GetOrCreateUserUseCase, GetUserByIdUseCase, GetUserByTgIdUseCase,
    ListUsersUseCase, UpdateUserUseCase,
    DeactivateUserUseCase, ActivateUserUseCase,
)
from app.core.user.general.exceptions import UserNotFoundError
from app.infra.user.general.repository_impl import UserRepositoryImpl
from .schemas import UserOut, UserGetOrCreateIn, UserGetOrCreateOut, UserUpdateIn

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/get-or-create", response_model=UserGetOrCreateOut, status_code=201)
async def get_or_create_user(body: UserGetOrCreateIn):
    """Вызывается при старте бота."""
    user, created = await GetOrCreateUserUseCase(UserRepositoryImpl()).execute(
        body.tg_id, body.name, body.second_name, body.username, body.avatar_url
    )
    return UserGetOrCreateOut(user=user, created=created)


@router.get("/", response_model=List[UserOut])
async def list_users():
    return await ListUsersUseCase(UserRepositoryImpl()).execute()


@router.get("/by-tg/{tg_id}", response_model=UserOut)
async def get_user_by_tg_id(tg_id: str):
    try:
        return await GetUserByTgIdUseCase(UserRepositoryImpl()).execute(tg_id)
    except UserNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    try:
        return await GetUserByIdUseCase(UserRepositoryImpl()).execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, body: UserUpdateIn):
    try:
        return await UpdateUserUseCase(UserRepositoryImpl()).execute(
            user_id, body.name, body.second_name, body.username, body.avatar_url
        )
    except UserNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(user_id: int):
    try:
        return await DeactivateUserUseCase(UserRepositoryImpl()).execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserOut)
async def activate_user(user_id: int):
    try:
        return await ActivateUserUseCase(UserRepositoryImpl()).execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(404, detail=str(e))
