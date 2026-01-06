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
    subj: TheorySubject
    id: Optional[int] = None
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)
    types: Optional[List[TheoryType]] = field(default_factory=list)
    
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


@dataclass
class TaskTheory:
    task_name: str
    theories: Optional[List[Theory]] = None
    task_id: Optional[int] = None
    
@dataclass
class TaskTheoryGroup:
    group_name: str
    is_single: bool
    tasks_theories: Optional[List["TaskTheory"]] = None
    task_group_id: Optional[int] = None