from asyncio.base_tasks import _task_get_stack
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.theory.enums import BlockType, TheoryType, TheorySubject

class SubjResponse(BaseModel):
    id: int
    name: TheorySubject

class TheoryTypesResponse(BaseModel):
    id: int
    name: TheoryType

class AllTheoryDopInfoResponse(BaseModel):
    id: int
    subject: TheorySubject
    types: List[TheoryTypesResponse]

class TheoryBlockResponse(BaseModel):
    id: int
    type: BlockType
    content: str
    order: int
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
    subject: TheorySubject
    type_ids: list[int]  # id типов теории


class TheoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    subject: Optional[TheorySubject] = None
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