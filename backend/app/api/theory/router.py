from urllib import response
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_factory
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import GetAllTheoryDopInfoUseCase, GetTheoryByIdUseCase, GetAllTheoriesForSubjectUseCase
from .schemas import AllTheoryDopInfoResponse, TheoryResponse, AllTheoryResponse, TaskGroupsResponse

router = APIRouter(prefix="/theory", tags=["Theory"])

@router.get("/all_theory_for_subject/{subject_id}", response_model=list[AllTheoryResponse])
async def get_all_theories(subject_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoriesForSubjectUseCase(repo)
    theories = await usecase.execute(subject_id)
    return theories


@router.get("/all_theory_dop_info", response_model=list[AllTheoryDopInfoResponse])
async def get_all_theory_dop_info():
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoryDopInfoUseCase(repo)
    theories = await usecase.execute()
    return theories


#TODO добавить входную модель, тк иначе пути по-тупому перекрываются
@router.get("/get_theory/{theory_id}", response_model=TheoryResponse)
async def get_theory(theory_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryByIdUseCase(repo)
    theory = await usecase.execute(theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory
    
    
@router.get("/get_tasks_theory_for_subject/{subject_id}", response_model=list[TaskGroupsResponse])
async def get_tasks_theory_for_subject(subject_id: int):
    pass