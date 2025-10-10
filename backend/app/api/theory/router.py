from urllib import response
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_factory
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import GetTheoryByIdUseCase, GetAllTheoriesUseCase
from .schemas import TheoryResponse, TheoryId

router = APIRouter(prefix="/theory", tags=["Theory"])

@router.get("/all_theory", response_model=list[str])
async def get_all_theories():
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoriesUseCase(repo)
    theories = await usecase.execute()
    return theories

#TODO добавить входную модель, тк иначе пути по-тупому перекрываются
@router.get("/get_theory", response_model=TheoryResponse)
async def get_theory(data: TheoryId):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryByIdUseCase(repo)
    theory = await usecase.execute(data.theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory
    
