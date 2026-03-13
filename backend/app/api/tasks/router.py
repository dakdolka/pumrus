from fastapi import APIRouter

from app.core.tasks.repository import ITaskRepository
from app.infra.tasks.general import TaskRepositoryImpl
# from app.core.tasks.use_cases import (

# )
# from .schemas import (

# )


router = APIRouter(prefix="/tasks", tags=["Tasks"])
repo: ITaskRepository = TaskRepositoryImpl()

