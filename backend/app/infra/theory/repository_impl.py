import sqlalchemy
from app.core.db import async_session_factory
from app.core.theory.entities import TaskTheory, TaskTheoryGroup, Theory, TheoryBlock, TheoryType
from app.core.theory.repository import ITheoryRepository
from app.core.theory.enums import BlockType
from .models import TaskTheoryAssociation, TaskTheoryBD, TheoryBD, TheoryBlockBD, TheoryTypeBD, TaskTheoryGroupBD
from app.core.db import async_session_factory
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, delete, insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


class TheoryRepositoryImpl(ITheoryRepository):
    
    async def get_all_theory_types(self, session: AsyncSession) -> List[dict]:
        stmt = select(TheoryTypeBD)
        result = await session.execute(stmt)
        res = result.scalars().all()
        return [el for el in res]
        
    async def create_theory(self, session: AsyncSession, theory: Theory) -> int:
        types = [
            (await session.scalars(
                select(TheoryTypeBD).where(TheoryTypeBD.name == typ.name)
            )).one() 
            for typ in theory.types
        ]
        # Создаём верхний объект
        bd_theory = TheoryBD(types=types, name=theory.name)
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
        return bd_theory
    
    async def insert_task_theory_group(self, session, task_theory_group: TaskTheoryGroup):
        group_bd = TaskTheoryGroupBD(
            name=task_theory_group.group_name,
            is_single=task_theory_group.is_single,
        )
        for task_dto in task_theory_group.tasks_theories or []:
            task_bd = TaskTheoryBD(
                name=task_dto.task_name,
            )
            for theory_bd in task_dto.theories or []:
                if theory_bd is not None:
                    task_bd.theories.append(theory_bd)
            group_bd.tasks_theories.append(task_bd)
        session.add(group_bd)
        await session.commit()
        return group_bd
    
    async def insert_task_theory_group(self, session, task_theory_group: TaskTheoryGroup):
        group_bd = TaskTheoryGroupBD(
            name=task_theory_group.group_name,
            is_single=task_theory_group.is_single,
        )
        
        for task_dto in task_theory_group.tasks_theories or []:
            task_bd = TaskTheoryBD(
                name=task_dto.task_name
            )
            group_bd.tasks_theories.append(task_bd)
        
        session.add(group_bd)
        await session.flush()
        
        # Вставляем Association Objects с order
        for task_dto in task_theory_group.tasks_theories or []:
            task_bd = group_bd.tasks_theories[task_theory_group.tasks_theories.index(task_dto)]
            for theory_with_order in task_dto.theories or []:
                association = TaskTheoryAssociation(
                    theory_id=theory_with_order.theory.id,
                    task_theory_id=task_bd.id,
                    order=theory_with_order.order
                )
                session.add(association)
        
        await session.commit()
        return group_bd


    async def get_all_theories(self, session: AsyncSession) -> List[tuple[int, str]]:
        stmt = select(TheoryBD).options(selectinload(TheoryBD.types))
        result = await session.execute(stmt)
        res = result.scalars().all()
        return res
    
    
    async def get_children_by_parent_id(self, session: AsyncSession, parent_id: int) -> List[TheoryBlockBD]:
        stmt = select(TheoryBlockBD).where(TheoryBlockBD.parent_id == parent_id).options(selectinload(TheoryBlockBD.children))
        result = await session.execute(stmt)
        res = result.scalars().all()
        for elem in res:
            if elem.children:
                elem.children = await self.get_children_by_parent_id(session, elem.id)
        return res
    
    async def get_theory_by_id(self, session: AsyncSession, id: int) -> Theory | None:
       stmt = select(TheoryBD).where(TheoryBD.id == id).options(selectinload(TheoryBD.blocks).selectinload(TheoryBlockBD.children))
       result = await session.execute(stmt)
       res = result.scalars().one_or_none()
       for block in res.blocks:
           if block.children:
                block.children = await self.get_children_by_parent_id(session, block.id)
       return res
    
    async def get_theories_by_names(self, session: AsyncSession, names: List[str]) -> List[TheoryBD]:
        stmt = select(TheoryBD).where(TheoryBD.name.in_(names))
        result = await session.execute(stmt)
        res = result.scalars().all()
        return res
    
    async def get_all_task_theory_groups(self, session: AsyncSession) -> list[TaskTheoryGroupBD]:
        stmt = (
            select(TaskTheoryGroupBD)
            .options(
                selectinload(TaskTheoryGroupBD.tasks_theories)
                .selectinload(TaskTheoryBD.theory_associations)
                .selectinload(TaskTheoryAssociation.theory)
            )
        )
        res = await session.execute(stmt)
        groups: list[TaskTheoryGroupBD] = res.scalars().all()
        def sort_task_group(group: TaskTheoryGroupBD):
            group.tasks_theories.sort(key=lambda t: int(t.name.replace('-', ' ').split()[0]))
            for task in group.tasks_theories:
                task.theory_associations.sort(key=lambda a: a.order)
        for group in groups:
            sort_task_group(group)
        groups.sort(key=lambda g: int(g.name.replace('-', ' ').split()[0]))
        return groups
    
    ##Форма
    
    async def create_theory_base(self, session: AsyncSession, name: str, type_ids: list[int]) -> TheoryBD:
        if type_ids:
            types_bd = (await session.execute(select(TheoryTypeBD).where(TheoryTypeBD.id.in_(type_ids)))).scalars().all()
        else:
            types_bd = []
        theory_bd = TheoryBD(name=name, types=list(types_bd))
        session.add(theory_bd)
        await session.flush()
        return theory_bd

    async def update_theory_base(self, session: AsyncSession, theory_id: int, name: Optional[str], type_ids: Optional[list[int]]) -> TheoryBD:
        res = await session.execute(select(TheoryBD).where(TheoryBD.id == theory_id).options(selectinload(TheoryBD.types)))
        theory_bd = res.scalars().one_or_none()
        if theory_bd is None:
            raise ValueError("Theory not found")
        if name is not None:
            theory_bd.name = name
        if type_ids is not None:
            types_bd = (await session.execute(select(TheoryTypeBD).where(TheoryTypeBD.id.in_(type_ids)))).scalars().all()
            theory_bd.types = list(types_bd)
        await session.flush()
        return theory_bd

    async def create_block(self, session: AsyncSession, theory_id: int, type: BlockType, content: str, parent_id: Optional[int], order: int) -> TheoryBlockBD:
        effective_theory_id = theory_id if parent_id is None else None
        block_bd = TheoryBlockBD(content=content, type=type, theory_id=effective_theory_id, parent_id=parent_id, order=order)
        session.add(block_bd)
        await session.flush()
        return block_bd

    async def update_block(self, session: AsyncSession, block_id: int, type: Optional[BlockType], content: Optional[str], parent_id: Optional[int], order: Optional[int]) -> TheoryBlockBD:
        res = await session.execute(select(TheoryBlockBD).where(TheoryBlockBD.id == block_id))
        block_bd = res.scalars().one_or_none()
        if block_bd is None:
            raise ValueError("Block not found")
        if type is not None:
            block_bd.type = type
        if content is not None:
            block_bd.content = content
        if parent_id is not None:
            block_bd.parent_id = parent_id
        if order is not None:
            block_bd.order = order
        await session.flush()
        return block_bd

    async def delete_block(self, session: AsyncSession, block_id: int) -> None:
        await session.execute(delete(TheoryBlockBD).where(TheoryBlockBD.id == block_id))
        
    async def update_task_theory_group(self, session: AsyncSession, group_id: int, name: Optional[str], is_single: Optional[bool]) -> TaskTheoryGroupBD:
        res = await session.execute(select(TaskTheoryGroupBD).where(TaskTheoryGroupBD.id == group_id))
        group_bd = res.scalars().one_or_none()
        if group_bd is None:
            raise ValueError("TaskTheoryGroup not found")
        if name is not None:
            group_bd.name = name
        if is_single is not None:
            group_bd.is_single = is_single
        await session.flush()
        return group_bd

    async def delete_task_theory_group(self, session: AsyncSession, group_id: int) -> None:
        await session.execute(delete(TaskTheoryBD).where(TaskTheoryBD.group_id == group_id))
        await session.execute(delete(TaskTheoryGroupBD).where(TaskTheoryGroupBD.id == group_id))
        
    async def insert_task_theory(self, session: AsyncSession, task: TaskTheory) -> TaskTheoryBD:
        task_bd = TaskTheoryBD(name=task.name, group_id=task.group_id)
        session.add(task_bd)
        await session.flush()
        return task_bd

    async def update_task_theory(self, session: AsyncSession, task_id: int, name: Optional[str], group_id: Optional[int]) -> TaskTheoryBD:
        res = await session.execute(select(TaskTheoryBD).where(TaskTheoryBD.id == task_id))
        task_bd = res.scalars().one_or_none()
        if task_bd is None:
            raise ValueError("TaskTheory not found")
        if name is not None:
            task_bd.name = name
        if group_id is not None:
            task_bd.group_id = group_id
        await session.flush()
        return task_bd

    async def delete_task_theory(self, session: AsyncSession, task_id: int) -> None:
        await session.execute(delete(TaskTheoryBD).where(TaskTheoryBD.id == task_id))
        
    async def replace_task_theory_links(self, session: AsyncSession, task_id: int, theory_ids: list[int]) -> None:
        await session.execute(delete(TaskTheoryAssociation).where(TaskTheoryAssociation.task_theory_id == task_id))
        for order_index, theory_id in enumerate(theory_ids):
            assoc = TaskTheoryAssociation(task_theory_id=task_id, theory_id=theory_id, order=order_index)
            session.add(assoc)
        await session.flush()
    
    async def insert_task_theory_group_from_request(self, session: AsyncSession, task_theory_group: TaskTheoryGroup):
        tg = TaskTheoryGroupBD(name=task_theory_group.group_name, is_single=task_theory_group.is_single)
        session.add(tg)
        await session.commit()
        

