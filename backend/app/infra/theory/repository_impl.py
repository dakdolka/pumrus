from ast import List
from app.core.db import async_session_factory
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.repository import ITheoryRepository
from .models import TheoryBD, TheoryBlockBD
from app.core.theory.enums import TheoryType, BlockType
from app.core.db import async_session_factory
from typing import List, Tuple
from sqlalchemy import insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

class TheoryRepositoryImpl(ITheoryRepository):
    async def create_theory(self, session: AsyncSession, theory: Theory) -> Tuple[int, List[int]]:
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
    
    async def get_all_theories(self, session: AsyncSession) -> List[tuple[int, str]]:
        stmt = select(TheoryBD.id, TheoryBD.name)
        result = await session.execute(stmt)
        res = result.all()
        print(res)
        return res
    
    
    async def get_theory_by_id(self, session: AsyncSession, id):
        stmt = (
            select(TheoryBD)
            .where(TheoryBD.id == id)
            .options(selectinload(TheoryBD.blocks))
        )

        result = await session.execute(stmt)
        orm_theory: TheoryBD = result.scalars().one_or_none()

        if orm_theory is None:
            return None

        blocks: List[TheoryBlock] = []
        for b in orm_theory.blocks:
            blocks.append(
                TheoryBlock(
                    id=b.id,
                    type=BlockType(b.type) if b.type is not None else None,
                    content=b.text,
                    theory_id=b.theory_id,
                )
            )

        domain_theory = Theory(
            id=orm_theory.id,
            name=orm_theory.name,
            type=TheoryType(orm_theory.type) if orm_theory.type is not None else None,
            blocks=blocks,
        )
        
        return domain_theory
    
    