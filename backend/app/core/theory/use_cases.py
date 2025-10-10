from .repository import ITheoryRepository
from .entities import Theory, TheoryBlock
from app.core.db import async_session_factory

class CreateTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, theory: Theory) -> Theory:
        async with async_session_factory() as session:
            async with session.begin():
                try:
                    new_id, block_ids =await self.repo.create_theory(session, theory)
                    theory.id = new_id
                    for i, block in enumerate(theory.blocks):
                        block.id = block_ids[i]
                    return theory
                except Exception as e:
                    print(e)