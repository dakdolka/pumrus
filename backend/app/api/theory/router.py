from urllib import response
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_factory
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import CreateTaskTheoryUseCase, CreateTasksTheoryUseCase, CreateTheoryBaseUseCase, CreateTheoryBlockUseCase, DeleteTaskTheoryGroupUseCase, DeleteTaskTheoryUseCase, DeleteTheoryBlockUseCase, GetAllTaskTheoryGroupsForSubjectUseCase, GetAllTheoryDopInfoUseCase, GetTheoryByIdUseCase, GetAllTheoriesForSubjectUseCase, UpdateTaskTheoryGroupUseCase, UpdateTaskTheoryLinksUseCase, UpdateTaskTheoryUseCase, UpdateTheoryBaseUseCase, UpdateTheoryBlockUseCase
from .schemas import AllTheoryDopInfoResponse, TaskTheoryCreateRequest, TaskTheoryGroupCreateRequest, TaskTheoryGroupUpdateRequest, TaskTheoryLinksUpdateRequest, TaskTheoryUpdateRequest, TheoryBlockCreateRequest, TheoryBlockUpdateRequest, TheoryCreateRequest, TheoryResponse, AllTheoryResponse, TaskGroupsResponse, TheoryUpdateRequest

router = APIRouter(prefix="/theory", tags=["Theory"])

@router.get("/all_theory_for_subject/{subject_id}", response_model=list[AllTheoryResponse])
async def get_all_theories(subject_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoriesForSubjectUseCase(repo)
    theories = await usecase.execute(subject_id)
    return theories


@router.get("/all_theory_dop_info", response_model=list[AllTheoryDopInfoResponse])
async def get_all_theory_dop_info():
    repo = TheoryRepositoryImpl()
    usecase = GetAllTheoryDopInfoUseCase(repo)
    theories = await usecase.execute()
    return theories


#TODO добавить входную модель, тк иначе пути по-тупому перекрываются
@router.get("/get_theory/{theory_id}", response_model=TheoryResponse)
async def get_theory(theory_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryByIdUseCase(repo)
    theory = await usecase.execute(theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory
    
    
@router.get("/get_tasks_theory_for_subject/{subject_id}", response_model=list[TaskGroupsResponse])
async def get_tasks_theory_for_subject(subject_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetAllTaskTheoryGroupsForSubjectUseCase(repo)
    theories = await usecase.execute(subject_id)
    return theories

### Форма

@router.post("/", response_model=TheoryResponse)
async def create_theory(body: TheoryCreateRequest):
    repo = TheoryRepositoryImpl()
    usecase = CreateTheoryBaseUseCase(repo)
    theory = await usecase.execute(body.name, body.subject, body.type_ids)
    return TheoryResponse(id=theory.id, name=theory.name, blocks=[])


@router.put("/{theory_id}", response_model=TheoryResponse)
async def update_theory(theory_id: int, body: TheoryUpdateRequest):
    repo = TheoryRepositoryImpl()
    usecase = UpdateTheoryBaseUseCase(repo)
    await usecase.execute(theory_id, body.name, body.subject, body.type_ids)
    get_usecase = GetTheoryByIdUseCase(repo)
    theory = await get_usecase.execute(theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory


@router.post("/{theory_id}/blocks")
async def create_block(theory_id: int, body: TheoryBlockCreateRequest):
    repo = TheoryRepositoryImpl()
    usecase = CreateTheoryBlockUseCase(repo)
    block = await usecase.execute(theory_id, body.type, body.content, body.parent_id, body.order)
    return {"id": block.id}


@router.put("/blocks/{block_id}")
async def update_block(block_id: int, body: TheoryBlockUpdateRequest):
    repo = TheoryRepositoryImpl()
    usecase = UpdateTheoryBlockUseCase(repo)
    block = await usecase.execute(block_id, body.type, body.content, body.parent_id, body.order)
    return {"id": block.id}


@router.delete("/blocks/{block_id}")
async def delete_block(block_id: int):
    repo = TheoryRepositoryImpl()
    usecase = DeleteTheoryBlockUseCase(repo)
    await usecase.execute(block_id)
    return {"success": True}

@router.post("/task-groups", response_model=dict)
async def create_task_group(body: TaskTheoryGroupCreateRequest):
    repo = TheoryRepositoryImpl()
    usecase = CreateTasksTheoryUseCase(repo)
    # здесь ты внутри usecase собираешь TaskTheoryGroup из body
    group_id = await usecase.execute(task_theory_group=body)  # адаптируй под свои entities
    return {"id": group_id}


@router.put("/task-groups/{group_id}", response_model=dict)
async def update_task_group(group_id: int, body: TaskTheoryGroupUpdateRequest):
    repo = TheoryRepositoryImpl()
    usecase = UpdateTaskTheoryGroupUseCase(repo)
    group = await usecase.execute(group_id, body.name, body.is_single)
    return {"id": group.id}


@router.delete("/task-groups/{group_id}", response_model=dict)
async def delete_task_group(group_id: int):
    repo = TheoryRepositoryImpl()
    usecase = DeleteTaskTheoryGroupUseCase(repo)
    await usecase.execute(group_id)
    return {"success": True}

@router.post("/task-groups/{group_id}/tasks", response_model=dict)
async def create_task(group_id: int, body: TaskTheoryCreateRequest):
    repo = TheoryRepositoryImpl()
    usecase = CreateTaskTheoryUseCase(repo)
    task = await usecase.execute(group_id, body.name)
    return {"id": task.id}


@router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: int, body: TaskTheoryUpdateRequest):
    repo = TheoryRepositoryImpl()
    usecase = UpdateTaskTheoryUseCase(repo)
    task = await usecase.execute(task_id, body.name, body.group_id)
    return {"id": task.id}


@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: int):
    repo = TheoryRepositoryImpl()
    usecase = DeleteTaskTheoryUseCase(repo)
    await usecase.execute(task_id)
    return {"success": True}

@router.put("/tasks/{task_id}/theories", response_model=dict)
async def update_task_theories(task_id: int, body: TaskTheoryLinksUpdateRequest):
    repo = TheoryRepositoryImpl()
    usecase = UpdateTaskTheoryLinksUseCase(repo)
    await usecase.execute(task_id, body.theory_ids)
    return {"success": True}
