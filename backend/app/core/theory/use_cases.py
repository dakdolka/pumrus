from pprint import pprint
from .repository import ITheoryRepository
from .entities import Theory, TheoryBlock, TheoryType, TheorySubject
from app.core.db import async_session_factory
from typing import Tuple, List

class CreateTheoryTypesAndSubjsUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
    
    async def execute(self, susbject2type_config: dict):
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.create_theory_types_and_subjs(session, susbject2type_config)

class CreateTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, theory: Theory) -> Tuple[int, List[int]]:
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.create_theory(session, theory)

class GetAllTheoryDopInfoUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self) -> List[dict]:
        async with async_session_factory() as session:
            res = await self.repo.get_all_theory_dop_info(session)
            res = [{"id": el[0], "subject": el[1].value, "types": [{"id":e.id, "name":e.name.value} for e in el[2]]} for el in res]
            pprint(res)
            return res

class GetTheoryByIdUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, id: int) -> Theory:
        async with async_session_factory() as session:
            theory = await self.repo.get_theory_by_id(session, id)
            return theory
        
class GetAllTheoriesForSubjectUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, subject_id) -> List[tuple[int, str]]:
        async with async_session_factory() as session:
            theories = await self.repo.get_all_theories_for_subject(session, subject_id)
            return theories
    