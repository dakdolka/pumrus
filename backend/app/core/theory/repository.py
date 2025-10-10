from abc import ABC
from .entities import Theory, TheoryBlock
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, List

class ITheoryRepository(ABC):
    async def create_theory(self, session: AsyncSession, theory: Theory) -> Tuple[int, List[int]]: ...