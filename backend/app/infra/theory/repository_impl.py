from app.core.db import async_session_factory
from app.core.theory.entities import Theory
from app.core.theory.repository import ITheoryRepository
from .models import TheoryBD, TheoryBlockBD
from app.core.theory.enums import TheoryType, BlockType
from app.core.db import async_session_factory
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

class TheoryRepositoryImpl(ITheoryRepository):
    
    async def create_theory(Self, session: AsyncSession, theory: Theory) -> None:
        stmt = insert(TheoryBD).values(type=theory.type, name=theory.name)
        result = await session.execute(stmt)
        await session.flush()
        new_id = result.lastrowid
        block_ids = []
        for block in theory.blocks:
            stmt = insert(TheoryBlockBD).values(type=block.type, text=block.content, theory_id=new_id)
            result = await session.execute(stmt)
            await session.flush()
            block.id = result.lastrowid
            block_ids.append(result.lastrowid)
        await session.commit()
        
        return new_id, block_ids