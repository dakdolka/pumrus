from pydantic import BaseModel
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