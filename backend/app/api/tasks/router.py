from typing import List

from fastapi import APIRouter, HTTPException

from app.core.tasks.repository import ITaskRepository
from app.infra.tasks.repository_impl import TaskRepositoryImpl
from app.core.tasks.use_cases import (
    CreateTaskUseCase,
    UpdateTaskUseCase,
    GetTaskByIdUseCase,
    GetTasksForSubjectUseCase,
    ReplaceTaskItemsUseCase,
    ParseRawContentUseCase,
)
from app.core.tasks.entities import TaskItem, Task
from app.core.theory.enums import TheorySubject
from .schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskDetailResponse,
    TaskItemDTO,
    ParseRawRequest,
    ParseRawResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# временно создаём репозиторий прямо тут; позже можно перевести на DI
repo: ITaskRepository = TaskRepositoryImpl()


@router.post("/", response_model=TaskResponse)
async def create_task(payload: TaskCreateRequest):
    usecase = CreateTaskUseCase(repo)
    task = await usecase.execute(
        name=payload.name,
        subject=TheorySubject(payload.subject_id),  # адаптируй под свой enum
        trainer_type=payload.trainer_type,
        input_mode=payload.input_mode,
    )
    return TaskResponse(
        id=task.id,
        name=task.name,
        subject_id=payload.subject_id,
        trainer_type=task.trainer_type,
        input_mode=task.input_mode,
        is_active=task.is_active,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: int):
    usecase = GetTaskByIdUseCase(repo)
    task = await usecase.execute(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDetailResponse(
        id=task.id,
        name=task.name,
        subject_id=task.subj.value if hasattr(task.subj, "value") else task.subj,
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


@router.get("/for_subject/{subject_id}", response_model=List[TaskResponse])
async def get_tasks_for_subject(subject_id: int):
    usecase = GetTasksForSubjectUseCase(repo)
    tasks = await usecase.execute(subject_id)
    return [
        TaskResponse(
            id=t.id,
            name=t.name,
            subject_id=subject_id,
            trainer_type=t.trainer_type,
            input_mode=t.input_mode,
            is_active=t.is_active,
        )
        for t in tasks
    ]


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
        subject_id=payload.subject_id,
        trainer_type=task.trainer_type,
        input_mode=task.input_mode,
        is_active=task.is_active,
    )


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
