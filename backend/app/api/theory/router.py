from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_factory
from app.core.theory.repository import TheoryRepositoryImpl
from app.core.theory.use_cases import GetTheoryUseCase
from .schemas import TheoryResponse

router = APIRouter(prefix="/theory", tags=["Theory"])

@router.get("/{theory_id}", response_model=TheoryResponse)
async def get_theory(theory_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryUseCase(repo)

    async with async_session_factory() as session:
        theory = await usecase.execute(theory_id)
        if not theory:
            raise HTTPException(status_code=404, detail="Theory not found")
        return theory