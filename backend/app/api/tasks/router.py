from typing import List

from fastapi import APIRouter, HTTPException

from app.core.tasks.repository import ITaskRepository
from app.infra.tasks.repository_impl import TaskRepositoryImpl
from app.core.tasks.use_cases import (
    CreateTaskUseCase,
    DeleteTaskUseCase,
    UpdateTaskUseCase,
    GetTaskByIdUseCase,
    GetAllTasksUseCase,
    ReplaceTaskItemsUseCase,
    ParseRawContentUseCase,
)
from app.core.tasks.entities import TaskItem
from .schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskDetailResponse,
    TaskItemDTO,
    ParseRawRequest,
    ParseRawResponse,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

repo: ITaskRepository = TaskRepositoryImpl()


@router.post("/", response_model=TaskResponse)
async def create_task(payload: TaskCreateRequest):
    usecase = CreateTaskUseCase(repo)
    task = await usecase.execute(
        name=payload.name,
        trainer_type=payload.trainer_type,
        input_mode=payload.input_mode,
    )
    return TaskResponse(
        id=task.id,
        name=task.name,
        trainer_type=task.trainer_type,
        input_mode=task.input_mode,
        is_active=task.is_active,
    )


@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks():
    usecase = GetAllTasksUseCase(repo)
    tasks = await usecase.execute()
    return [
        TaskResponse(
            id=t.id,
            name=t.name,
            trainer_type=t.trainer_type,
            input_mode=t.input_mode,
            is_active=t.is_active,
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: int):
    usecase = GetTaskByIdUseCase(repo)
    task = await usecase.execute(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDetailResponse(
        id=task.id,
        name=task.name,
        trainer_type=task.trainer_type,
        input_mode=task.input_mode,
        is_active=task.is_active,
        items=[
            TaskItemDTO(
                id=i.id,
                order=i.order,
                trainer_type=i.trainer_type,
                raw=i.raw,
                visible=i.visible,
                correct_option=i.correct_option,
                correct_visible=i.correct_visible,
                extra=i.extra or {},
            )
            for i in task.items
        ],
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, payload: TaskCreateRequest):
    usecase = UpdateTaskUseCase(repo)
    task = await usecase.execute(
        task_id=task_id,
        name=payload.name,
        trainer_type=payload.trainer_type,
        input_mode=payload.input_mode,
        is_active=payload.is_active,
    )
    return TaskResponse(
        id=task.id,
        name=task.name,
        trainer_type=task.trainer_type,
        input_mode=task.input_mode,
        is_active=task.is_active,
    )

@router.delete("/{task_id}")
async def delete_task_by_id(task_id: int):
    usecase = DeleteTaskUseCase(repo)
    await usecase.execute(task_id)

@router.put("/{task_id}/items")
async def replace_task_items(task_id: int, items: List[TaskItemDTO]):
    usecase = ReplaceTaskItemsUseCase(repo)
    domain_items = [
        TaskItem(
            id=i.id,
            task_id=task_id,
            order=i.order,
            trainer_type=i.trainer_type,
            raw=i.raw,
            visible=i.visible,
            correct_option=i.correct_option,
            correct_visible=i.correct_visible,
            extra=i.extra,
        )
        for i in items
    ]
    await usecase.execute(task_id, domain_items)
    return {"success": True}


@router.post("/parse-raw", response_model=ParseRawResponse)
async def parse_raw(request: ParseRawRequest):
    usecase = ParseRawContentUseCase()
    items = await usecase.execute(
        trainer_type=request.trainer_type,
        raw_content=request.raw_content,
        task_id=0,
    )
    return ParseRawResponse(
        items=[
            TaskItemDTO(
                id=None,
                order=i.order,
                trainer_type=i.trainer_type,
                raw=i.raw,
                visible=i.visible,
                correct_option=i.correct_option,
                correct_visible=i.correct_visible,
                extra=i.extra or {},
            )
            for i in items
        ]
    )
