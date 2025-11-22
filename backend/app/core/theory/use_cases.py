from .repository import ITheoryRepository
from .entities import Theory, TheoryBlock
from app.core.db import async_session_factory
from typing import Tuple, List

class CreateTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, theory: Theory) -> Tuple[int, List[int]]:
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.create_theory(session, theory)


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
            print(theories)
            return theories
    