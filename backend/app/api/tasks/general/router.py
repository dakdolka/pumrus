from fastapi import APIRouter, HTTPException
from typing import List

from app.core.tasks.general.exceptions import (
    TaskNotFoundError, TaskItemNotFoundError,
    OptionSetNotFoundError, OptionNotFoundError, TaskGroupNotFoundError,
)
from app.core.tasks.general.use_cases import (
    ListTaskGroupsUseCase, GetTaskGroupByIdUseCase,
    CreateTaskGroupUseCase, UpdateTaskGroupUseCase, DeleteTaskGroupUseCase,
    ListOptionsUseCase, CreateOptionUseCase, UpdateOptionUseCase, DeleteOptionUseCase,
    ListOptionSetsUseCase, GetOptionSetByIdUseCase,
    CreateOptionSetUseCase, UpdateOptionSetUseCase, DeleteOptionSetUseCase,
    ListTasksUseCase, ListTasksByGroupUseCase, GetTaskByIdUseCase,
    CreateTaskUseCase, UpdateTaskUseCase, DeleteTaskUseCase,
    CreateTaskItemUseCase, UpdateTaskItemUseCase, DeleteTaskItemUseCase,
)
from app.infra.tasks.general.repository_impl import (
    TaskRepositoryImpl, TaskItemRepositoryImpl,
    OptionRepositoryImpl, OptionSetRepositoryImpl, TaskGroupRepositoryImpl,
)
from .schemas import (
    TaskGroupOut, TaskGroupCreateIn, TaskGroupUpdateIn,
    OptionOut, OptionCreateIn, OptionUpdateIn,
    OptionSetOut, OptionSetCreateIn, OptionSetUpdateIn,
    TaskOut, TaskCreateIn, TaskUpdateIn,
    TaskItemOut, TaskItemCreateIn, TaskItemUpdateIn,
)

router = APIRouter(prefix="/tasks/general", tags=["tasks-general"])


# ── TaskGroup ─────────────────────────────────────────────────────────────────

@router.get("/groups", response_model=List[TaskGroupOut])
async def list_task_groups():
    return await ListTaskGroupsUseCase(TaskGroupRepositoryImpl()).execute()


@router.post("/groups", response_model=TaskGroupOut, status_code=201)
async def create_task_group(body: TaskGroupCreateIn):
    return await CreateTaskGroupUseCase(TaskGroupRepositoryImpl()).execute(body.name)


@router.put("/groups/{group_id}", response_model=TaskGroupOut)
async def update_task_group(group_id: int, body: TaskGroupUpdateIn):
    try:
        return await UpdateTaskGroupUseCase(TaskGroupRepositoryImpl()).execute(group_id, body.name)
    except TaskGroupNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/groups/{group_id}", status_code=204)
async def delete_task_group(group_id: int):
    try:
        await DeleteTaskGroupUseCase(TaskGroupRepositoryImpl()).execute(group_id)
    except TaskGroupNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── Option ────────────────────────────────────────────────────────────────────

@router.get("/options", response_model=List[OptionOut])
async def list_options():
    return await ListOptionsUseCase(OptionRepositoryImpl()).execute()


@router.post("/options", response_model=OptionOut, status_code=201)
async def create_option(body: OptionCreateIn):
    return await CreateOptionUseCase(OptionRepositoryImpl()).execute(body.content, body.extras)


@router.put("/options/{option_id}", response_model=OptionOut)
async def update_option(option_id: int, body: OptionUpdateIn):
    try:
        return await UpdateOptionUseCase(OptionRepositoryImpl()).execute(
            option_id, body.content, body.extras
        )
    except OptionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/options/{option_id}", status_code=204)
async def delete_option(option_id: int):
    try:
        await DeleteOptionUseCase(OptionRepositoryImpl()).execute(option_id)
    except OptionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── OptionSet ─────────────────────────────────────────────────────────────────

@router.get("/option-sets", response_model=List[OptionSetOut])
async def list_option_sets():
    return await ListOptionSetsUseCase(OptionSetRepositoryImpl()).execute()


@router.get("/option-sets/{set_id}", response_model=OptionSetOut)
async def get_option_set(set_id: int):
    try:
        return await GetOptionSetByIdUseCase(OptionSetRepositoryImpl()).execute(set_id)
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/option-sets", response_model=OptionSetOut, status_code=201)
async def create_option_set(body: OptionSetCreateIn):
    return await CreateOptionSetUseCase(OptionSetRepositoryImpl()).execute(
        body.name, body.option_ids
    )


@router.put("/option-sets/{set_id}", response_model=OptionSetOut)
async def update_option_set(set_id: int, body: OptionSetUpdateIn):
    try:
        return await UpdateOptionSetUseCase(OptionSetRepositoryImpl()).execute(
            set_id, body.name, body.option_ids
        )
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/option-sets/{set_id}", status_code=204)
async def delete_option_set(set_id: int):
    try:
        await DeleteOptionSetUseCase(OptionSetRepositoryImpl()).execute(set_id)
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── Task ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TaskOut])
async def list_tasks():
    return await ListTasksUseCase(TaskRepositoryImpl()).execute()


@router.get("/by-group/{group_id}", response_model=List[TaskOut])
async def list_tasks_by_group(group_id: int):
    return await ListTasksByGroupUseCase(TaskRepositoryImpl()).execute(group_id)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int):
    try:
        return await GetTaskByIdUseCase(TaskRepositoryImpl()).execute(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(body: TaskCreateIn):
    return await CreateTaskUseCase(TaskRepositoryImpl()).execute(
        body.name, body.task_group_id, body.default_option_set_id
    )


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: TaskUpdateIn):
    try:
        return await UpdateTaskUseCase(TaskRepositoryImpl()).execute(
            task_id, body.name, body.task_group_id, body.default_option_set_id
        )
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int):
    try:
        await DeleteTaskUseCase(TaskRepositoryImpl()).execute(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── TaskItem ──────────────────────────────────────────────────────────────────

@router.post("/{task_id}/items", response_model=TaskItemOut, status_code=201)
async def create_task_item(task_id: int, body: TaskItemCreateIn):
    try:
        return await CreateTaskItemUseCase(
            TaskRepositoryImpl(), TaskItemRepositoryImpl()
        ).execute(
            task_id,
            body.content_raw, body.content_visible, body.content_correct,
            body.correct_option_id, body.option_set_override_id,
            body.notice_wrong, body.notice_right,
        )
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.put("/items/{item_id}", response_model=TaskItemOut)
async def update_task_item(item_id: int, body: TaskItemUpdateIn):
    try:
        return await UpdateTaskItemUseCase(TaskItemRepositoryImpl()).execute(
            item_id,
            body.content_raw, body.content_visible, body.content_correct,
            body.correct_option_id, body.option_set_override_id,
            body.notice_wrong, body.notice_right,
        )
    except TaskItemNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/items/{item_id}", status_code=204)
async def delete_task_item(item_id: int):
    try:
        await DeleteTaskItemUseCase(TaskItemRepositoryImpl()).execute(item_id)
    except TaskItemNotFoundError as e:
        raise HTTPException(404, detail=str(e))
