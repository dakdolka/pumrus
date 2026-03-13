import sqlalchemy
from app.core.db import async_session_factory
from app.core.theory.entities import TaskTheory, TaskTheoryGroup, Theory, TheoryBlock, TheoryType
from app.core.theory.repository import ITheoryRepository
from app.core.theory.enums import BlockType
from .models import TaskTheoryAssociation, TaskTheoryBD, TheoryBD, TheoryBlockBD, TheoryTypeBD, TaskTheoryGroupBD
from app.core.db import async_session_factory
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, delete, insert, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession