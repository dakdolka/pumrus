from dataclasses import dataclass, field
from typing import Optional, List
from .enums import BlockType, TheoryType

@dataclass
class TheoryBlock:
    id: Optional[int]
    type: BlockType
    content: str
    theory_id: int
    
@dataclass
class Theory:
    id: Optional[int]
    name: str
    type: TheoryType
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)