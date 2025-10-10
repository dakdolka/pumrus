from abc import ABC
from .entities import Theory, TheoryBlock
from sqlalchemy.ext.asyncio import AsyncSession

class ITheoryRepository(ABC):
    async def create_theory(self, session: AsyncSession, theory: Theory) -> None: ...