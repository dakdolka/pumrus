from ast import List
from pprint import pprint

import sqlalchemy
from app.core.db import async_session_factory
from app.core.theory.entities import TaskTheoryGroup, Theory, TheoryBlock, TheoryType, TheorySubject
from app.core.theory.repository import ITheoryRepository
from .models import TaskTheoryAssociation, TaskTheoryBD, TheoryBD, TheoryBlockBD, TheoryTypeBD, TheorySubjectBD, TaskTheoryGroupBD
from app.core.db import async_session_factory
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


class TheoryRepositoryImpl(ITheoryRepository):
    async def create_theory_types_and_subjs(self, session: AsyncSession, subject2type_config: dict):
        for subj, types in subject2type_config.items():
            subj = TheorySubjectBD(name=subj)
            session.add(subj)
            for typ in types:
                session.add(TheoryTypeBD(name=typ, subject=subj))
        await session.commit()
        
    async def create_theory(self, session: AsyncSession, theory: Theory, subj: TheorySubject | None) -> int:
        types = [
            (await session.scalars(
                select(TheoryTypeBD).where(TheoryTypeBD.name == typ.name)
            )).one() 
            for typ in theory.types
        ]
        if subj is None:
            subj = (await session.scalars(
                select(TheorySubjectBD).where(TheorySubjectBD.name == theory.subj.name)
            )).first()
        # Создаём верхний объект
        bd_theory = TheoryBD(types=types, subject_id=subj.id, name=theory.name)
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
            subject_id=task_theory_group.subject.id
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
            subject_id=task_theory_group.subject.id
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




    async def get_all_theories_for_subject(self, session: AsyncSession, subject_id: int) -> List[tuple[int, str]]:
        stmt = select(TheoryBD).where(and_(TheoryBD.subject_id == subject_id, TheoryBD.types.any())).options(selectinload(TheoryBD.types))
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
   
    async def get_all_theory_dop_info(self, session: AsyncSession) -> List[dict]:
        stmt = select(TheorySubjectBD).options(selectinload(TheorySubjectBD.types))
        result = await session.execute(stmt)
        res = result.scalars().all()
        return [(el.id, el.name, el.types) for el in res]
    
    async def get_theories_by_names(self, session: AsyncSession, names: List[str]) -> List[TheoryBD]:
        stmt = select(TheoryBD).where(TheoryBD.name.in_(names))
        result = await session.execute(stmt)
        res = result.scalars().all()
        return res
    
    async def get_all_subjects(self, session: AsyncSession, subject_id: int | None) -> List[TheorySubject]:
        if subject_id is None:
            stmt = select(TheorySubjectBD)
        else:
            stmt = select(TheorySubjectBD).where(TheorySubjectBD.id==subject_id)
        res = await session.execute(stmt)
        res = res.scalars().all()
        return res
    
    async def get_all_task_groups_for_subject(self, session: AsyncSession, subject_id: int) -> list[TaskTheoryGroupBD]:
        stmt = (
            select(TaskTheoryGroupBD)
            .where(TaskTheoryGroupBD.subject_id == subject_id)
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


        