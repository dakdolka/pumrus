from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.db import get_db
from app.core.tasks.general.exceptions import (
    TaskNotFoundError, TaskItemNotFoundError,
    OptionSetNotFoundError, OptionNotFoundError, TaskGroupNotFoundError,
)
from app.core.tasks.general.use_cases import (
    ListTaskGroupsUseCase, GetTaskGroupByIdUseCase,
    CreateTaskGroupUseCase, UpdateTaskGroupUseCase, DeleteTaskGroupUseCase,
    ListOptionsUseCase, GetOptionByContentUseCase, GetOrCreateOptionUseCase,
    CreateOptionUseCase, UpdateOptionUseCase, DeleteOptionUseCase,
    ListOptionSetsUseCase, GetOptionSetByIdUseCase,
    CreateOptionSetUseCase, UpdateOptionSetUseCase, DeleteOptionSetUseCase,
    ListTasksUseCase, ListTasksByGroupUseCase, GetTaskByIdUseCase,
    CreateTaskUseCase, UpdateTaskUseCase, DeleteTaskUseCase,
    CreateTaskItemUseCase, CreateTaskItemsBulkUseCase,
    UpdateTaskItemUseCase, UpdateTaskItemsBulkUseCase, DeleteTaskItemUseCase,
)
from app.core.tasks.parsers.parse_use_case import ParseRawUseCase
from app.infra.tasks.general.repository_impl import (
    TaskRepositoryImpl, TaskItemRepositoryImpl,
    OptionRepositoryImpl, OptionSetRepositoryImpl, TaskGroupRepositoryImpl,
)
from .schemas import (
    TaskGroupOut, TaskGroupCreateIn, TaskGroupUpdateIn,
    OptionOut, OptionCreateIn, OptionUpdateIn, OptionGetOrCreateOut,
    OptionSetOut, OptionSetCreateIn, OptionSetUpdateIn,
    TaskOut, TaskCreateIn, TaskUpdateIn,
    TaskItemOut, TaskItemCreateIn, TaskItemUpdateIn,
    TaskItemBulkUpdateIn, ParseRawIn, ParsedItemOut,
)

router = APIRouter(prefix="/tasks/general", tags=["tasks-general"])


# ── TaskGroup ─────────────────────────────────────────────────────────────────

@router.get("/groups", response_model=List[TaskGroupOut])
async def list_task_groups(db: AsyncSession = Depends(get_db)):
    return await ListTaskGroupsUseCase(TaskGroupRepositoryImpl(), db).execute()


@router.post("/groups", response_model=TaskGroupOut, status_code=201)
async def create_task_group(body: TaskGroupCreateIn,
                            db: AsyncSession = Depends(get_db)):
    return await CreateTaskGroupUseCase(TaskGroupRepositoryImpl(), db).execute(body.name)


@router.put("/groups/{group_id}", response_model=TaskGroupOut)
async def update_task_group(group_id: int, body: TaskGroupUpdateIn,
                            db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateTaskGroupUseCase(TaskGroupRepositoryImpl(), db).execute(
            group_id, body.name
        )
    except TaskGroupNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/groups/{group_id}", status_code=204)
async def delete_task_group(group_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteTaskGroupUseCase(TaskGroupRepositoryImpl(), db).execute(group_id)
    except TaskGroupNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── Option ────────────────────────────────────────────────────────────────────

@router.get("/options", response_model=List[OptionOut])
async def list_options(content: Optional[str] = None,
                       db: AsyncSession = Depends(get_db)):
    if content:
        result = await GetOptionByContentUseCase(OptionRepositoryImpl(), db).execute(content)
        return [result] if result else []
    return await ListOptionsUseCase(OptionRepositoryImpl(), db).execute()


@router.post("/options/get-or-create", response_model=OptionGetOrCreateOut)
async def get_or_create_option(body: OptionCreateIn,
                               db: AsyncSession = Depends(get_db)):
    option, created = await GetOrCreateOptionUseCase(
        OptionRepositoryImpl(), db
    ).execute(body.content, body.extras)
    return OptionGetOrCreateOut(option=option, created=created)


@router.post("/options", response_model=OptionOut, status_code=201)
async def create_option(body: OptionCreateIn, db: AsyncSession = Depends(get_db)):
    return await CreateOptionUseCase(OptionRepositoryImpl(), db).execute(
        body.content, body.extras
    )


@router.put("/options/{option_id}", response_model=OptionOut)
async def update_option(option_id: int, body: OptionUpdateIn,
                        db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateOptionUseCase(OptionRepositoryImpl(), db).execute(
            option_id, body.content, body.extras
        )
    except OptionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/options/{option_id}", status_code=204)
async def delete_option(option_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteOptionUseCase(OptionRepositoryImpl(), db).execute(option_id)
    except OptionNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── OptionSet ─────────────────────────────────────────────────────────────────

@router.get("/option-sets", response_model=List[OptionSetOut])
async def list_option_sets(db: AsyncSession = Depends(get_db)):
    return await ListOptionSetsUseCase(OptionSetRepositoryImpl(), db).execute()


@router.get("/option-sets/{set_id}", response_model=OptionSetOut)
async def get_option_set(set_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await GetOptionSetByIdUseCase(OptionSetRepositoryImpl(), db).execute(set_id)
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/option-sets", response_model=OptionSetOut, status_code=201)
async def create_option_set(body: OptionSetCreateIn,
                            db: AsyncSession = Depends(get_db)):
    return await CreateOptionSetUseCase(OptionSetRepositoryImpl(), db).execute(
        body.name, body.option_ids
    )


@router.put("/option-sets/{set_id}", response_model=OptionSetOut)
async def update_option_set(set_id: int, body: OptionSetUpdateIn,
                            db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateOptionSetUseCase(OptionSetRepositoryImpl(), db).execute(
            set_id, body.name, body.option_ids
        )
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/option-sets/{set_id}", status_code=204)
async def delete_option_set(set_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteOptionSetUseCase(OptionSetRepositoryImpl(), db).execute(set_id)
    except OptionSetNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── Task ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    return await ListTasksUseCase(TaskRepositoryImpl(), db).execute()


@router.get("/by-group/{group_id}", response_model=List[TaskOut])
async def list_tasks_by_group(group_id: int, db: AsyncSession = Depends(get_db)):
    return await ListTasksByGroupUseCase(TaskRepositoryImpl(), db).execute(group_id)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await GetTaskByIdUseCase(TaskRepositoryImpl(), db).execute(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(body: TaskCreateIn, db: AsyncSession = Depends(get_db)):
    return await CreateTaskUseCase(TaskRepositoryImpl(), db).execute(
        body.name, body.task_group_id, body.default_option_set_id
    )


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: TaskUpdateIn,
                      db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateTaskUseCase(TaskRepositoryImpl(), db).execute(
            task_id, body.name, body.task_group_id, body.default_option_set_id
        )
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteTaskUseCase(TaskRepositoryImpl(), db).execute(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── TaskItem ──────────────────────────────────────────────────────────────────

@router.post("/{task_id}/items", response_model=TaskItemOut, status_code=201)
async def create_task_item(task_id: int, body: TaskItemCreateIn,
                           db: AsyncSession = Depends(get_db)):
    try:
        return await CreateTaskItemUseCase(
            TaskRepositoryImpl(), TaskItemRepositoryImpl(), db
        ).execute(
            task_id, body.content_raw, body.content_visible, body.content_correct,
            body.correct_option_id, body.option_set_override_id,
            body.notice_wrong, body.notice_right,
        )
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.post("/{task_id}/items/bulk", response_model=List[TaskItemOut], status_code=201)
async def create_task_items_bulk(task_id: int, body: List[TaskItemCreateIn],
                                 db: AsyncSession = Depends(get_db)):
    try:
        return await CreateTaskItemsBulkUseCase(
            TaskRepositoryImpl(), TaskItemRepositoryImpl(), db
        ).execute(task_id, body)
    except TaskNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.put("/items/bulk", response_model=List[TaskItemOut])
async def update_task_items_bulk(body: List[TaskItemBulkUpdateIn],
                                 db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateTaskItemsBulkUseCase(TaskItemRepositoryImpl(), db).execute(body)
    except TaskItemNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.put("/items/{item_id}", response_model=TaskItemOut)
async def update_task_item(item_id: int, body: TaskItemUpdateIn,
                           db: AsyncSession = Depends(get_db)):
    try:
        return await UpdateTaskItemUseCase(TaskItemRepositoryImpl(), db).execute(
            item_id, body.content_raw, body.content_visible, body.content_correct,
            body.correct_option_id, body.option_set_override_id,
            body.notice_wrong, body.notice_right,
        )
    except TaskItemNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.delete("/items/{item_id}", status_code=204)
async def delete_task_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await DeleteTaskItemUseCase(TaskItemRepositoryImpl(), db).execute(item_id)
    except TaskItemNotFoundError as e:
        raise HTTPException(404, detail=str(e))


# ── Parse ─────────────────────────────────────────────────────────────────────

@router.post("/parse-raw", response_model=List[ParsedItemOut])
async def parse_raw(body: ParseRawIn, db: AsyncSession = Depends(get_db)):
    """Парсит raw-массив. Ничего не сохраняет. Нотисы добавляются вручную на фронте."""
    try:
        return await ParseRawUseCase(db).execute(
            body.parser_type, body.raw_items, body.option_set_id
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
