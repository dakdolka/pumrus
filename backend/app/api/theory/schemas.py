from asyncio.base_tasks import _task_get_stack
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.theory.enums import BlockType, TheoryType

class TheoryTypesResponse(BaseModel):
    id: int
    name: TheoryType

class AllTheoryDopInfoResponse(BaseModel):
    id: int
    types: List[TheoryTypesResponse]

class TheoryBlockResponse(BaseModel):
    id: int
    type: BlockType
    content: str
    order: int
    parent_id: Optional[int] = None
    theory_id: Optional[int] = None
    children: List["TheoryBlockResponse"] = []

class TheoryResponse(BaseModel):
    id: int
    name: str
    blocks: List[TheoryBlockResponse]

class AllTheoryResponse(BaseModel):
    id: int
    name: str
    types: list[TheoryTypesResponse]
    
class TheoryId(BaseModel):
    theory_id: int

class TheoryForTaskTheory(BaseModel):
    theory_id: int
    theory_name: str = Field(example="Местоимения")

class TaskTheory(BaseModel):
    task_id: int
    task_name: str = Field(example="1 На месте пропуска...")
    theories: List[TheoryForTaskTheory]
    
class TaskGroupsResponse(BaseModel):
    task_group_id: int
    group_name: str = Field(example="1-3 Мини-текст")
    is_single: bool
    tasks: List[TaskTheory]
    
### Форма

class TheoryCreateRequest(BaseModel):
    name: str
    type_ids: list[int]  # id типов теории


class TheoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    type_ids: Optional[list[int]] = None


class TheoryBlockCreateRequest(BaseModel):
    type: BlockType
    content: str
    parent_id: Optional[int] = None
    order: int


class TheoryBlockUpdateRequest(BaseModel):
    type: Optional[BlockType] = None
    content: Optional[str] = None
    order: Optional[int] = None
    parent_id: Optional[int] = None
    

#Форма для теории по заданиям
class TaskTheoryGroupCreateRequest(BaseModel):
    name: str = Field(..., example="Уравнения 7 класс")
    is_single: bool = Field(..., description="True, если в группе всегда одна задача активна")


class TaskTheoryGroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, example="Новое имя группы")
    is_single: Optional[bool] = Field(None)


class TaskTheoryCreateRequest(BaseModel):
    name: str = Field(..., example="Задача 1")
    # group_id берём из URL, поэтому здесь не нужен


class TaskTheoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, example="Новое имя задачи")
    group_id: Optional[int] = Field(
        None,
        description="Если передан, переносим задачу в другую группу",
    )


class TaskTheoryLinksUpdateRequest(BaseModel):
    theory_ids: List[int] = Field(
        ...,
        description="Список id теорий в нужном порядке для данной задачи",
        example=[1, 5, 7],
    )