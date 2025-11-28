from .repository import ITheoryRepository
from .entities import Theory, TheoryBlock, TheoryType, TheorySubject
from app.core.db import async_session_factory
from typing import Tuple, List

class CreateTheoryTypesAndSubjsUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
    
    async def execute(self, theory_types: List[TheoryType], theory_subjs: List[TheorySubject]):
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.create_theory_types_and_subjs(session, theory_types, theory_subjs)

class CreateTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, theory: Theory) -> Tuple[int, List[int]]:
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.create_theory(session, theory)

class GetAllSubjectsUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self) -> List[tuple[int, str]]:
        async with async_session_factory() as session:
            subjs = await self.repo.get_all_subjects(session)
            
            return subjs

class GetTheoryByIdUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, id: int) -> Theory:
        async with async_session_factory() as session:
            theory = await self.repo.get_theory_by_id(session, id)
            return theory
        
class GetAllTheoriesUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self) -> List[tuple[int, str]]:
        async with async_session_factory() as session:
            theories = await self.repo.get_all_theories(session)
            return theories
    