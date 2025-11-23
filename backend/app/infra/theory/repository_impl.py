from ast import List
from pprint import pprint
from app.core.db import async_session_factory
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.repository import ITheoryRepository
from .models import TheoryBD, TheoryBlockBD
from app.core.theory.enums import TheoryType, BlockType
from app.core.db import async_session_factory
from typing import List, Optional, Tuple
from sqlalchemy import insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

class TheoryRepositoryImpl(ITheoryRepository):
    async def create_theory(self, session: AsyncSession, theory: Theory):
    # Создаём верхний объект
        bd_theory = TheoryBD(type=theory.type, name=theory.name)
        session.add(bd_theory)  # ORM теперь знает сессию для top-level
        
        # Рекурсивно создаём блоки
        def _map_blocks_to_bd(block: TheoryBlock, parent: Optional[TheoryBlockBD] = None) -> TheoryBlockBD:
            bd_block = TheoryBlockBD(
                content=block.content,
                type=block.type,
                order=block.order,
                parent=parent,
                theory=bd_theory if parent is None else None  # только верхний уровень получает theory
            )
            # создаём детей
            bd_block.children = [_map_blocks_to_bd(child, bd_block) for child in block.children]
            return bd_block

        # Присваиваем блоки верхнему уровню
        bd_theory.blocks = [_map_blocks_to_bd(block) for block in theory.blocks]

        await session.commit()
       
        
    async def get_all_theories(self, session: AsyncSession) -> List[tuple[int, str]]:
        stmt = select(TheoryBD.id, TheoryBD.name)
        result = await session.execute(stmt)
        res = result.all()
        print(res)
        return res
    
    
    async def get_children_by_parent_id(self, session: AsyncSession, parent_id: int) -> List[TheoryBlockBD]:
        # print("parent_id", parent_id)
        stmt = select(TheoryBlockBD).where(TheoryBlockBD.parent_id == parent_id).options(selectinload(TheoryBlockBD.children))
        result = await session.execute(stmt)
        res = result.scalars().all()
        print("Children reached")
        for elem in res:
            if elem.children:
                elem.children = await self.get_children_by_parent_id(session, elem.id)
        return res
    
    async def get_theory_by_id(self, session: AsyncSession, id: int) -> Theory | None:
       stmt = select(TheoryBD).where(TheoryBD.id == id).options(selectinload(TheoryBD.blocks).selectinload(TheoryBlockBD.children))
       result = await session.execute(stmt)
       res = result.scalars().one_or_none()
       print("res blocks orm")
       pprint(res.blocks)
       for block in res.blocks:
           print('block children orm view')
           pprint(block.children)
           if block.children:
                block.children = await self.get_children_by_parent_id(session, block.id)
       return res
    