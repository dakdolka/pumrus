from urllib import response
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_factory
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import GetAllTheoryTypesBySubjectUseCase, GetTheoryByIdUseCase, GetAllTheoriesUseCase, GetAllSubjectsUseCase
from .schemas import AllSubjResponse, TheoryResponse, TheoryId, AllTheoryResponse, AllTheoryTypesResponse

router = APIRouter(prefix="/theory", tags=["Theory"])

@router.get("/all_theory", response_model=list[AllTheoryResponse])
async def get_all_theories():
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoriesUseCase(repo)
    theories = await usecase.execute()
    return theories


@router.get("/all_subjects", response_model=list[AllSubjResponse])
async def get_all_subjects():
    repo = TheoryRepositoryImpl()
    usecase = GetAllSubjectsUseCase(repo)
    subjects = await usecase.execute()
    return subjects


@router.get("/all_theory_types/{subject}", response_model=list[AllTheoryTypesResponse])
async def get_all_theory_types_by_subject(subject_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoryTypesBySubjectUseCase(repo)
    types = await usecase.execute(subject_id)
    return types

#TODO добавить входную модель, тк иначе пути по-тупому перекрываются
@router.get("/get_theory/{theory_id}", response_model=TheoryResponse)
async def get_theory(theory_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryByIdUseCase(repo)
    theory = await usecase.execute(theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory
    
