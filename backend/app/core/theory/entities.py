from dataclasses import dataclass, field
import types
from typing import Optional, List
from .enums import BlockType, TheoryType, TheorySubject

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
    types: List[TheoryType]
    subj: TheorySubject
    id: Optional[int] = None
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)
    
@dataclass
class AllTheory:
    id: Optional[int]
    name: str
    types: List[TheoryType]
    
@dataclass
class TheorySubject:
    name: TheorySubject
    id: Optional[int] = None
    
@dataclass
class TheoryType:
    name: TheoryType
    id: Optional[int] = None