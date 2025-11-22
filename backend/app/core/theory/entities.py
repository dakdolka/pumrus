from dataclasses import dataclass, field
from typing import Optional, List
from .enums import BlockType, TheoryType

@dataclass
class TheoryBlock:
    type: BlockType
    content: str
    order: int
    theory_id: Optional[int] = None
    id: Optional[int] = None
    children: List[Optional["TheoryBlock"]] = field(default_factory=list)
    
    
@dataclass
class Theory:
    name: str
    type: TheoryType
    id: Optional[int] = None
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)
    
@dataclass
class AllTheory:
    id: Optional[int]
    name: str