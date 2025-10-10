from pydantic import BaseModel
from typing import List
from app.core.theory.enums import BlockType, TheoryType

class TheoryBlockResponse(BaseModel):
    id: int
    type: BlockType
    content: str
    theory_id: int

class TheoryResponse(BaseModel):
    id: int
    name: str
    type: TheoryType
    blocks: List[TheoryBlockResponse]