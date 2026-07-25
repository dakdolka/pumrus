from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.infra.catalog.models import (
    CourseVersionBD,
    ExamTaskBD,
    ExamTaskTopicBD,
    TopicBD,
)
from app.infra.content.models import (
    TheoryBlockV2BD,
    TheoryDocumentBD,
    TheoryDocumentVersionBD,
)


router = APIRouter(prefix="/v2/admin", tags=["v2-admin"])


class CatalogUpdateIn(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    short_description: str | None = Field(default=None, max_length=1024)


class TopicCreateIn(CatalogUpdateIn):
    exam_task_id: int


class DocumentCreateIn(BaseModel):
    owner_type: Literal["task", "topic"]
    owner_id: int
    title: str = Field(min_length=1, max_length=256)


class BlockCreateIn(BaseModel):
    block_type: str = Field(min_length=1, max_length=32)
    parent_block_id: int | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0


class BlockUpdateIn(BaseModel):
    block_type: str | None = Field(default=None, min_length=1, max_length=32)
    parent_block_id: int | None = None
    data: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    sort_order: int | None = None


class LiveBlockIn(BaseModel):
    client_id: str = Field(min_length=1, max_length=96)
    parent_client_id: str | None = Field(default=None, max_length=96)
    block_type: str = Field(min_length=1, max_length=32)
    data: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0


class LivePublishIn(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    owner_title: str = Field(min_length=1, max_length=256)
    owner_description: str | None = Field(default=None, max_length=1024)
    blocks: list[LiveBlockIn]


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = settings.admin_token
    if expected and (
        not x_admin_key
        or not secrets.compare_digest(x_admin_key, expected)
    ):
        raise HTTPException(401, "Неверный ключ доступа")


@router.get("/status")
async def admin_status():
    return {"requiresAuth": bool(settings.admin_token)}


def _block_out(block: TheoryBlockV2BD) -> dict[str, Any]:
    return {
        "id": block.id,
        "parentId": block.parent_block_id,
        "type": block.block_type,
        "schemaVersion": block.schema_version,
        "data": block.data,
        "settings": block.settings,
        "sortOrder": block.sort_order,
    }


async def _document_out(
    db: AsyncSession,
    document: TheoryDocumentBD,
) -> dict[str, Any]:
    versions = (
        await db.scalars(
            select(TheoryDocumentVersionBD)
            .where(TheoryDocumentVersionBD.document_id == document.id)
            .order_by(TheoryDocumentVersionBD.version_number.desc())
        )
    ).all()
    editing = None
    if document.published_version_id is not None:
        editing = next(
            (
                version
                for version in versions
                if version.id == document.published_version_id
            ),
            None,
        )
    if editing is None:
        editing = next(
            (version for version in versions if version.status == "draft"),
            None,
        )
    blocks = []
    if editing is not None:
        blocks = list(
            (
                await db.scalars(
                    select(TheoryBlockV2BD)
                    .where(TheoryBlockV2BD.document_version_id == editing.id)
                    .order_by(TheoryBlockV2BD.sort_order, TheoryBlockV2BD.id)
                )
            ).all()
        )
    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "ownerType": "task" if document.exam_task_id is not None else "topic",
        "ownerId": document.exam_task_id or document.topic_id,
        "publishedVersionId": document.published_version_id,
        "editingVersion": None if editing is None else {
            "id": editing.id,
            "number": editing.version_number,
            "status": editing.status,
        },
        "versions": [
            {
                "id": version.id,
                "number": version.version_number,
                "status": version.status,
                "publishedAt": version.published_at,
            }
            for version in versions
        ],
        "blocks": [_block_out(block) for block in blocks],
    }


@router.get("/catalog", dependencies=[Depends(require_admin)])
async def admin_catalog(db: AsyncSession = Depends(get_db)):
    course_version = await db.scalar(
        select(CourseVersionBD).where(CourseVersionBD.is_active.is_(True))
    )
    if course_version is None:
        raise HTTPException(409, "Активная версия курса не найдена")
    tasks = list(
        (
            await db.scalars(
                select(ExamTaskBD)
                .where(ExamTaskBD.course_version_id == course_version.id)
                .order_by(ExamTaskBD.sort_order, ExamTaskBD.number)
            )
        ).all()
    )
    links = (
        await db.execute(
            select(ExamTaskTopicBD, TopicBD)
            .join(TopicBD, TopicBD.id == ExamTaskTopicBD.topic_id)
            .where(TopicBD.course_version_id == course_version.id)
            .order_by(
                ExamTaskTopicBD.exam_task_id,
                ExamTaskTopicBD.sort_order,
                TopicBD.title,
            )
        )
    ).all()
    topics_by_task: dict[int, list[dict[str, Any]]] = {}
    for link, topic in links:
        topics_by_task.setdefault(link.exam_task_id, []).append(
            {
                "id": topic.id,
                "code": topic.code,
                "title": topic.title,
                "shortDescription": topic.short_description,
                "status": topic.status,
            }
        )
    return {
        "courseVersion": {
            "id": course_version.id,
            "code": course_version.code,
            "title": course_version.title,
        },
        "tasks": [
            {
                "id": task.id,
                "number": task.number,
                "title": task.title,
                "shortDescription": task.short_description,
                "status": task.status,
                "topics": topics_by_task.get(task.id, []),
            }
            for task in tasks
        ],
    }


@router.patch("/tasks/{task_id}", dependencies=[Depends(require_admin)])
async def update_task(
    task_id: int,
    body: CatalogUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(ExamTaskBD, task_id)
    if task is None:
        raise HTTPException(404, "Задание не найдено")
    task.title = body.title.strip()
    task.short_description = body.short_description
    await db.commit()
    return {"id": task.id, "title": task.title}


@router.post("/topics", status_code=201, dependencies=[Depends(require_admin)])
async def create_topic(
    body: TopicCreateIn,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(ExamTaskBD, body.exam_task_id)
    if task is None:
        raise HTTPException(404, "Задание не найдено")
    topic = TopicBD(
        course_version_id=task.course_version_id,
        code=f"topic-{uuid.uuid4().hex[:12]}",
        title=body.title.strip(),
        short_description=body.short_description,
        status="published",
    )
    db.add(topic)
    await db.flush()
    max_order = await db.scalar(
        select(func.max(ExamTaskTopicBD.sort_order)).where(
            ExamTaskTopicBD.exam_task_id == task.id
        )
    )
    db.add(
        ExamTaskTopicBD(
            exam_task_id=task.id,
            topic_id=topic.id,
            sort_order=int(max_order or 0) + 1,
            is_primary=True,
        )
    )
    await db.commit()
    return {"id": topic.id, "title": topic.title}


@router.patch("/topics/{topic_id}", dependencies=[Depends(require_admin)])
async def update_topic(
    topic_id: int,
    body: CatalogUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    topic = await db.get(TopicBD, topic_id)
    if topic is None:
        raise HTTPException(404, "Тема не найдена")
    topic.title = body.title.strip()
    topic.short_description = body.short_description
    await db.commit()
    return {"id": topic.id, "title": topic.title}


@router.get("/theory-documents", dependencies=[Depends(require_admin)])
async def get_document_for_owner(
    owner_type: Literal["task", "topic"],
    owner_id: int,
    db: AsyncSession = Depends(get_db),
):
    condition = (
        TheoryDocumentBD.exam_task_id == owner_id
        if owner_type == "task"
        else TheoryDocumentBD.topic_id == owner_id
    )
    document = await db.scalar(select(TheoryDocumentBD).where(condition))
    if document is None:
        return None
    return await _document_out(db, document)


@router.post(
    "/theory-documents",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_document(
    body: DocumentCreateIn,
    db: AsyncSession = Depends(get_db),
):
    document = TheoryDocumentBD(
        exam_task_id=body.owner_id if body.owner_type == "task" else None,
        topic_id=body.owner_id if body.owner_type == "topic" else None,
        title=body.title.strip(),
        status="draft",
    )
    db.add(document)
    await db.flush()
    await db.commit()
    return await _document_out(db, document)


@router.post(
    "/theory-documents/{document_id}/publish-live",
    dependencies=[Depends(require_admin)],
)
async def publish_live_document(
    document_id: int,
    body: LivePublishIn,
    db: AsyncSession = Depends(get_db),
):
    document = await db.get(TheoryDocumentBD, document_id)
    if document is None:
        raise HTTPException(404, "Документ не найден")
    if not body.blocks:
        raise HTTPException(409, "Нельзя опубликовать пустой документ")

    client_ids = [block.client_id for block in body.blocks]
    if len(client_ids) != len(set(client_ids)):
        raise HTTPException(400, "Идентификаторы блоков должны быть уникальными")
    known_ids = set(client_ids)
    parents = {
        block.client_id: block.parent_client_id
        for block in body.blocks
    }
    for block_id, parent_id in parents.items():
        if parent_id is not None and parent_id not in known_ids:
            raise HTTPException(400, "Родительский блок не входит в документ")
        visited = {block_id}
        cursor = parent_id
        while cursor is not None:
            if cursor in visited:
                raise HTTPException(400, "Вложенность блоков содержит цикл")
            visited.add(cursor)
            cursor = parents.get(cursor)

    owner = (
        await db.get(ExamTaskBD, document.exam_task_id)
        if document.exam_task_id is not None
        else await db.get(TopicBD, document.topic_id)
    )
    if owner is None:
        raise HTTPException(409, "Владелец документа не найден")

    latest_number = await db.scalar(
        select(func.max(TheoryDocumentVersionBD.version_number)).where(
            TheoryDocumentVersionBD.document_id == document.id
        )
    )
    now = datetime.now(timezone.utc)
    version = TheoryDocumentVersionBD(
        document_id=document.id,
        version_number=int(latest_number or 0) + 1,
        status="published",
        published_at=now,
    )
    db.add(version)
    await db.flush()

    created: dict[str, TheoryBlockV2BD] = {}
    for item in body.blocks:
        block = TheoryBlockV2BD(
            document_version_id=version.id,
            block_type=item.block_type,
            schema_version=1,
            data=item.data,
            settings=item.settings,
            sort_order=item.sort_order,
        )
        db.add(block)
        await db.flush()
        created[item.client_id] = block
    for item in body.blocks:
        if item.parent_client_id is not None:
            created[item.client_id].parent_block_id = created[
                item.parent_client_id
            ].id

    previous = [
        item
        for item in (
            await db.scalars(
                select(TheoryDocumentVersionBD).where(
                    TheoryDocumentVersionBD.document_id == document.id,
                    TheoryDocumentVersionBD.id != version.id,
                )
            )
        ).all()
        if item.status == "published"
    ]
    for item in previous:
        item.status = "archived"

    document.title = body.title.strip()
    document.published_version_id = version.id
    document.status = "published"
    owner.title = body.owner_title.strip()
    owner.short_description = body.owner_description
    await db.commit()
    return await _document_out(db, document)


@router.post(
    "/theory-documents/{document_id}/draft",
    dependencies=[Depends(require_admin)],
)
async def create_draft(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    document = await db.get(TheoryDocumentBD, document_id)
    if document is None:
        raise HTTPException(404, "Документ не найден")
    existing = await db.scalar(
        select(TheoryDocumentVersionBD).where(
            TheoryDocumentVersionBD.document_id == document.id,
            TheoryDocumentVersionBD.status == "draft",
        )
    )
    if existing is not None:
        return await _document_out(db, document)
    latest_number = await db.scalar(
        select(func.max(TheoryDocumentVersionBD.version_number)).where(
            TheoryDocumentVersionBD.document_id == document.id
        )
    )
    version = TheoryDocumentVersionBD(
        document_id=document.id,
        version_number=int(latest_number or 0) + 1,
        status="draft",
    )
    db.add(version)
    await db.flush()

    if document.published_version_id is not None:
        source_blocks = list(
            (
                await db.scalars(
                    select(TheoryBlockV2BD)
                    .where(
                        TheoryBlockV2BD.document_version_id
                        == document.published_version_id
                    )
                    .order_by(TheoryBlockV2BD.id)
                )
            ).all()
        )
        clones: dict[int, TheoryBlockV2BD] = {}
        for source in source_blocks:
            clone = TheoryBlockV2BD(
                document_version_id=version.id,
                block_type=source.block_type,
                schema_version=source.schema_version,
                data=dict(source.data),
                settings=dict(source.settings),
                sort_order=source.sort_order,
            )
            db.add(clone)
            await db.flush()
            clones[source.id] = clone
        for source in source_blocks:
            if source.parent_block_id in clones:
                clones[source.id].parent_block_id = clones[
                    source.parent_block_id
                ].id
    await db.commit()
    return await _document_out(db, document)


async def _draft_version(
    db: AsyncSession,
    document_id: int,
) -> TheoryDocumentVersionBD:
    version = await db.scalar(
        select(TheoryDocumentVersionBD).where(
            TheoryDocumentVersionBD.document_id == document_id,
            TheoryDocumentVersionBD.status == "draft",
        )
    )
    if version is None:
        raise HTTPException(409, "Сначала создайте черновик")
    return version


@router.post(
    "/theory-documents/{document_id}/blocks",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_block(
    document_id: int,
    body: BlockCreateIn,
    db: AsyncSession = Depends(get_db),
):
    version = await _draft_version(db, document_id)
    if body.parent_block_id is not None:
        parent = await db.get(TheoryBlockV2BD, body.parent_block_id)
        if parent is None or parent.document_version_id != version.id:
            raise HTTPException(400, "Родительский блок не принадлежит черновику")
    block = TheoryBlockV2BD(
        document_version_id=version.id,
        parent_block_id=body.parent_block_id,
        block_type=body.block_type,
        schema_version=1,
        data=body.data,
        settings=body.settings,
        sort_order=body.sort_order,
    )
    db.add(block)
    await db.commit()
    return _block_out(block)


@router.patch("/blocks/{block_id}", dependencies=[Depends(require_admin)])
async def update_block(
    block_id: int,
    body: BlockUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    block = await db.get(TheoryBlockV2BD, block_id)
    if block is None:
        raise HTTPException(404, "Блок не найден")
    version = await db.get(TheoryDocumentVersionBD, block.document_version_id)
    if version is None or version.status != "draft":
        raise HTTPException(409, "Опубликованную версию нельзя изменять")
    values = body.model_dump(exclude_unset=True)
    if "parent_block_id" in values and values["parent_block_id"] is not None:
        parent_id = values["parent_block_id"]
        if parent_id == block.id:
            raise HTTPException(400, "Блок не может быть родителем самого себя")
        parent = await db.get(TheoryBlockV2BD, parent_id)
        if parent is None or parent.document_version_id != block.document_version_id:
            raise HTTPException(400, "Родитель принадлежит другому документу")
        visited = {block.id}
        cursor = parent
        while cursor is not None:
            if cursor.id in visited:
                raise HTTPException(400, "Нельзя создать циклическую вложенность")
            visited.add(cursor.id)
            cursor = (
                await db.get(TheoryBlockV2BD, cursor.parent_block_id)
                if cursor.parent_block_id is not None
                else None
            )
    mapping = {
        "block_type": "block_type",
        "parent_block_id": "parent_block_id",
        "data": "data",
        "settings": "settings",
        "sort_order": "sort_order",
    }
    for source, target in mapping.items():
        if source in values:
            setattr(block, target, values[source])
    await db.commit()
    return _block_out(block)


@router.delete("/blocks/{block_id}", dependencies=[Depends(require_admin)])
async def delete_block(
    block_id: int,
    db: AsyncSession = Depends(get_db),
):
    block = await db.get(TheoryBlockV2BD, block_id)
    if block is None:
        raise HTTPException(404, "Блок не найден")
    version = await db.get(TheoryDocumentVersionBD, block.document_version_id)
    if version is None or version.status != "draft":
        raise HTTPException(409, "Опубликованную версию нельзя изменять")
    await db.delete(block)
    await db.commit()
    return {"deleted": True}


@router.post(
    "/theory-documents/{document_id}/publish",
    dependencies=[Depends(require_admin)],
)
async def publish_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    document = await db.get(TheoryDocumentBD, document_id)
    if document is None:
        raise HTTPException(404, "Документ не найден")
    version = await _draft_version(db, document.id)
    block_count = await db.scalar(
        select(func.count(TheoryBlockV2BD.id)).where(
            TheoryBlockV2BD.document_version_id == version.id
        )
    )
    if not block_count:
        raise HTTPException(409, "Нельзя опубликовать пустой документ")
    now = datetime.now(timezone.utc)
    version.status = "published"
    version.published_at = now
    document.published_version_id = version.id
    document.status = "published"
    await db.commit()
    return await _document_out(db, document)
