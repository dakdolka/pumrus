from pprint import pprint

from app.api.theory.schemas import TaskGroupsResponse, TaskTheory as TaskTheoryResponse, TheoryForTaskTheory
from app.core.theory.enums import BlockType
from .repository import ITheoryRepository
from .entities import Theory, TheoryBlock, TheoryType, TheorySubject, TaskTheoryGroup, TaskTheory
from app.core.db import async_session_factory
from typing import Optional, Tuple, List

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

    async def execute(self, theory: Theory, subject: TheorySubject | None = None) -> int:
        async with async_session_factory() as session:
            async with session.begin():
                res = await self.repo.create_theory(session, theory, subject)
                return res
class GetAllTheoryDopInfoUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self) -> List[dict]:
        async with async_session_factory() as session:
            res = await self.repo.get_all_theory_dop_info(session)
            res = sorted([{"id": el[0], "subject": el[1].value, "types": [{"id":e.id, "name":e.name.value} for e in el[2]]} for el in res], key=lambda x: x["id"])
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
    
class GetAllTaskGroupsForSubjectUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, subject_id) -> List[TaskTheoryGroup]:
        async with async_session_factory() as session:
            theories = await self.repo.get_all_task_groups_for_subject(session, subject_id)
            return theories
        
class CreateTasksTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, task_theory_group: TaskTheoryGroup):
         async with async_session_factory() as session:
              async with session.begin():
                  res = await self.repo.insert_task_theory_group(session, task_theory_group)
                  return res
    
class GetTheoriesByNamesUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
        
    async def execute(self, names: List[str]) -> List[int]:
        async with async_session_factory() as session:
            theories = await self.repo.get_theories_by_names(session, names)
            return theories

class GetAllTaskTheoryGroupsForSubjectUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
    
    async def execute(self, subject_id: int) -> List[TaskGroupsResponse]:
        async with async_session_factory() as session:
            res = await self.repo.get_all_task_groups_for_subject(session, subject_id)
            ans: list[TaskGroupsResponse] = []

            for elem in res:
                group = TaskGroupsResponse(
                    task_group_id=elem.id,
                    group_name=elem.name,
                    is_single=elem.is_single,
                    tasks=[]
                )

                for el in elem.tasks_theories:
                    # associations уже отсортированы по order в репозитории
                    theories = [
                        TheoryForTaskTheory(
                            theory_id=assoc.theory.id,
                            theory_name=assoc.theory.name
                        )
                        for assoc in el.theory_associations
                    ]

                    taskth = TaskTheoryResponse(
                        task_id=el.id,
                        task_name=el.name,
                        theories=theories
                    )
                    group.tasks.append(taskth)
                ans.append(group)
            return ans


class GetSubjectByIdUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo
    
    async def execute(self, subject_id: int | None) -> List[TheorySubject]:
        async with async_session_factory() as session:
            all_subjs = await self.repo.get_all_subjects(session, subject_id)
            return all_subjs
        
class CreateTheoryBaseUseCase:
    def __init__(self, repo: ITheoryRepository): self.repo = repo
    async def execute(self, name: str, subject: TheorySubject, type_ids: list[int]):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create_theory_base(session, name, subject, type_ids)


class UpdateTheoryBaseUseCase:
    def __init__(self, repo: ITheoryRepository): self.repo = repo
    async def execute(self, theory_id: int, name: Optional[str], subject: Optional[TheorySubject], type_ids: Optional[list[int]]):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.update_theory_base(session, theory_id, name, subject, type_ids)


class CreateTheoryBlockUseCase:
    def __init__(self, repo: ITheoryRepository): self.repo = repo
    async def execute(self, theory_id: int, type: BlockType, content: str, parent_id: Optional[int], order: int):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create_block(session, theory_id, type, content, parent_id, order)


class UpdateTheoryBlockUseCase:
    def __init__(self, repo: ITheoryRepository): self.repo = repo
    async def execute(self, block_id: int, type: Optional[BlockType], content: Optional[str], parent_id: Optional[int], order: Optional[int]):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.update_block(session, block_id, type, content, parent_id, order)


class DeleteTheoryBlockUseCase:
    def __init__(self, repo: ITheoryRepository): self.repo = repo
    async def execute(self, block_id: int):
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.delete_block(session, block_id)
                
class UpdateTaskTheoryGroupUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, group_id: int, name: Optional[str], is_single: Optional[bool]):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.update_task_theory_group(
                    session,
                    group_id=group_id,
                    name=name,
                    is_single=is_single,
                )


class DeleteTaskTheoryGroupUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, group_id: int):
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.delete_task_theory_group(session, group_id)
                
class CreateTaskTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, group_id: int, name: str) -> int:
        async with async_session_factory() as session:
            async with session.begin():
                # TaskTheory – доменная сущность. Если её нет, можно просто прокинуть параметры в репо.
                task = TaskTheory(
                    id=None,
                    name=name,
                    group_id=group_id,
                    theory_associations=[],  # или не заполнять, если в entity нет
                )
                res = await self.repo.insert_task_theory(session, task)
                return res


class UpdateTaskTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, task_id: int, name: Optional[str], group_id: Optional[int]):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.update_task_theory(
                    session,
                    task_id=task_id,
                    name=name,
                    group_id=group_id,
                )


class DeleteTaskTheoryUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, task_id: int):
        async with async_session_factory() as session:
            async with session.begin():
                await self.repo.delete_task_theory(session, task_id)


class UpdateTaskTheoryLinksUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, task_id: int, theory_ids: list[int]):
        async with async_session_factory() as session:
            async with session.begin():
                # Полностью переопределяем список связей для задачи
                await self.repo.replace_task_theory_links(
                    session,
                    task_id=task_id,
                    theory_ids=theory_ids,
                )
