from dataclasses import dataclass, field
import types
from typing import Any, Optional, List
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
    id: Optional[int] = None
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)
    types: Optional[List[TheoryType]] = field(default_factory=list)
    
@dataclass
class AllTheory:
    id: Optional[int]
    name: str
    types: List[TheoryType]
    
@dataclass
class TheoryType:
    name: TheoryType
    id: Optional[int] = None

@dataclass
class TaskTheoryWithOrder:
    theory: Any
    order: int

@dataclass
class TaskTheory:
    task_name: str
    theories: Optional[List[TaskTheoryWithOrder]] = None  # ← с порядком
    id: Optional[int] = None
    
@dataclass
class TaskTheoryGroup:
    group_name: str
    is_single: bool
    tasks_theories: Optional[List["TaskTheory"]] = None
    id: Optional[int] = None