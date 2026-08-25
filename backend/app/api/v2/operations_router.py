from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.admin_router import require_admin
from app.core.config import settings
from app.core.db import get_db
from app.core.monetization import validate_telegram_init_data
from app.infra.catalog.models import ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.infra.content.models import TheoryBlockV2BD, TheoryDocumentBD
from app.infra.exercises.models import (
    ExerciseBD,
    ExerciseSetBD,
    ExerciseSetItemBD,
    ExerciseTaskLinkBD,
    ExerciseTopicLinkBD,
    ExerciseVersionBD,
)
from app.infra.monetization.models import (
    AccessPolicyBD,
    AccessPolicyResourceBD,
    EntitlementBD,
    PaymentOrderBD,
    ProductBD,
    PriceBD,
    SubscriptionBD,
)
from app.infra.practice.models import AttemptV2BD, PracticeSessionBD
from app.infra.system.models import AdminAuditLogBD, AppSettingBD, MediaAssetBD
from app.infra.user.general.models import UserBD


admin_router = APIRouter(
    prefix="/v2/admin/operations",
    tags=["v2-admin-operations"],
    dependencies=[Depends(require_admin)],
)
public_router = APIRouter(prefix="/v2", tags=["v2-system"])

DEFAULT_APP_SETTINGS: dict[str, Any] = {
    "homeTitleLine": "Русский язык —",
    "homeTitleAccent": "это легко",
    "theorySubtitle": "Разобраться в правилах",
    "practiceSubtitle": "Проверить себя",
    "footerLabel": "UmRus · подготовка к ЕГЭ",
    "contactUrl": "https://t.me/dak_dolka",
    "projectDescription": (
        "UmRus помогает последовательно изучать правила русского языка "
        "и сразу закреплять их на практике."
    ),
    "maintenanceNotice": "",
}
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
ALLOWED_INTERACTIONS = {
    "single_choice",
    "multiple_choice",
    "text_input",
    "vowel_fill",
    "stress_selection",
}


class AppSettingsIn(BaseModel):
    home_title_line: str = Field(min_length=1, max_length=80)
    home_title_accent: str = Field(min_length=1, max_length=80)
    theory_subtitle: str = Field(min_length=1, max_length=120)
    practice_subtitle: str = Field(min_length=1, max_length=120)
    footer_label: str = Field(min_length=1, max_length=160)
    contact_url: str = Field(min_length=1, max_length=512)
    project_description: str = Field(min_length=1, max_length=1500)
    maintenance_notice: str = Field(default="", max_length=500)

    @field_validator("contact_url")
    @classmethod
    def validate_contact_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.startswith(("https://", "http://")):
            raise ValueError("Ссылка для связи должна начинаться с https:// или http://")
        return cleaned


class ExerciseSetCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    exam_task_id: int
    topic_id: int | None = None
    status: Literal["draft", "published", "archived"] = "draft"
    access_level: Literal["free", "preview", "premium"] = "free"
    selection_strategy: Literal["all_shuffled", "least_seen_first", "ordered"] = "least_seen_first"
    session_size: int = Field(default=50, ge=1, le=100)
    page_size: int = Field(default=5, ge=1, le=20)


class ExerciseSetUpdateIn(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    topic_id: int | None = None
    status: Literal["draft", "published", "archived"]
    access_level: Literal["free", "preview", "premium"]
    selection_strategy: Literal["all_shuffled", "least_seen_first", "ordered"]


class ExerciseVersionIn(BaseModel):
    interaction_type: str = Field(min_length=1, max_length=64)
    prompt_data: dict[str, Any]
    interaction_config: dict[str, Any] = Field(default_factory=dict)
    answer_config: dict[str, Any]
    checker_type: str = Field(min_length=1, max_length=64)
    checker_config: dict[str, Any] = Field(default_factory=dict)
    feedback_data: dict[str, Any] = Field(default_factory=dict)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    source: str | None = Field(default=None, max_length=256)
    exam_task_ids: list[int] | None = Field(default=None, max_length=10)
    topic_ids: list[int] | None = Field(default=None, max_length=20)


class ManualGrantIn(BaseModel):
    user_id: int
    product_id: int
    ends_at: datetime | None = None
    note: str = Field(default="Выдано владельцем", max_length=512)


class UserStatusIn(BaseModel):
    is_active: bool


def _app_settings_out(value: dict[str, Any] | None) -> dict[str, Any]:
    return {**DEFAULT_APP_SETTINGS, **(value or {})}


async def _settings_record(db: AsyncSession) -> AppSettingBD | None:
    return await db.get(AppSettingBD, "public_app")


@public_router.get("/app-config")
async def public_app_config(db: AsyncSession = Depends(get_db)):
    record = await _settings_record(db)
    return _app_settings_out(record.value if record else None)


@public_router.post("/auth/telegram")
async def authenticate_telegram(request: Request, db: AsyncSession = Depends(get_db)):
    raw_data = request.headers.get("X-Telegram-Init-Data", "")
    if not raw_data:
        raise HTTPException(401, "Откройте приложение через Telegram")
    telegram_user = validate_telegram_init_data(raw_data)
    telegram_id = str(telegram_user["id"])
    user = await db.scalar(select(UserBD).where(UserBD.tg_id == telegram_id))
    if user is None:
        user = UserBD(
            tg_id=telegram_id,
            name=telegram_user.get("first_name") or "Ученик",
            second_name=telegram_user.get("last_name") or "",
            username=telegram_user.get("username"),
            avatar_url=telegram_user.get("photo_url"),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
    else:
        user.name = telegram_user.get("first_name") or user.name
        user.second_name = telegram_user.get("last_name") or ""
        user.username = telegram_user.get("username")
        user.avatar_url = telegram_user.get("photo_url")
        user.last_active_at = datetime.now(timezone.utc)
    if not user.is_active:
        raise HTTPException(403, "Доступ к приложению ограничен")
    await db.commit()
    return {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "telegramId": user.tg_id,
    }


@public_router.get("/media/{public_id}")
async def public_media(public_id: str, db: AsyncSession = Depends(get_db)):
    asset = await db.scalar(
        select(MediaAssetBD).where(
            MediaAssetBD.public_id == public_id,
            MediaAssetBD.status == "active",
        )
    )
    if asset is None:
        raise HTTPException(404, "Файл не найден")
    path = settings.media_root / asset.storage_name
    if not path.is_file():
        raise HTTPException(404, "Файл отсутствует в хранилище")
    return FileResponse(
        path,
        media_type=asset.content_type,
        filename=asset.original_name,
        content_disposition_type="inline",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@admin_router.get("/settings")
async def get_app_settings(db: AsyncSession = Depends(get_db)):
    record = await _settings_record(db)
    return _app_settings_out(record.value if record else None)


@admin_router.get("/export")
async def export_owner_configuration(db: AsyncSession = Depends(get_db)):
    record = await _settings_record(db)
    products = list((await db.scalars(select(ProductBD).order_by(ProductBD.id))).all())
    prices = list((await db.scalars(select(PriceBD).order_by(PriceBD.id))).all())
    resources = list((await db.scalars(
        select(AccessPolicyResourceBD).order_by(AccessPolicyResourceBD.id)
    )).all())
    media = list((await db.scalars(select(MediaAssetBD).order_by(MediaAssetBD.id))).all())
    payload = {
        "schema": "umrus-owner-configuration",
        "version": 1,
        "exportedAt": datetime.now(timezone.utc),
        "appSettings": _app_settings_out(record.value if record else None),
        "products": [{
            "id": item.id,
            "code": item.code,
            "title": item.title,
            "description": item.description,
            "billingType": item.billing_type,
            "status": item.status,
            "accessPolicyId": item.access_policy_id,
        } for item in products],
        "prices": [{
            "id": item.id,
            "productId": item.product_id,
            "provider": item.provider,
            "currency": item.currency,
            "amount": item.amount,
            "status": item.status,
        } for item in prices],
        "resources": [{
            "accessPolicyId": item.access_policy_id,
            "resourceType": item.resource_type,
            "resourceId": item.resource_id,
        } for item in resources],
        "media": [{
            "publicId": item.public_id,
            "name": item.original_name,
            "contentType": item.content_type,
            "sizeBytes": item.size_bytes,
            "altText": item.alt_text,
            "status": item.status,
        } for item in media],
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return JSONResponse(
        jsonable_encoder(payload),
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="umrus-settings-{stamp}.json"',
        },
    )


@admin_router.put("/settings")
async def update_app_settings(body: AppSettingsIn, db: AsyncSession = Depends(get_db)):
    value = {
        "homeTitleLine": body.home_title_line.strip(),
        "homeTitleAccent": body.home_title_accent.strip(),
        "theorySubtitle": body.theory_subtitle.strip(),
        "practiceSubtitle": body.practice_subtitle.strip(),
        "footerLabel": body.footer_label.strip(),
        "contactUrl": body.contact_url.strip(),
        "projectDescription": body.project_description.strip(),
        "maintenanceNotice": body.maintenance_notice.strip(),
    }
    record = await _settings_record(db)
    if record is None:
        record = AppSettingBD(
            key="public_app",
            value=value,
            description="Public application copy and support links",
        )
        db.add(record)
    else:
        record.value = value
    await db.commit()
    return _app_settings_out(value)


@admin_router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    async def count(model, *conditions):
        return int(await db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)

    dangling_sets = int(await db.scalar(
        select(func.count()).select_from(ExerciseSetBD).where(
            ~select(ExerciseSetItemBD.id)
            .where(ExerciseSetItemBD.exercise_set_id == ExerciseSetBD.id)
            .exists()
        )
    ) or 0)
    unpublished_docs = await count(
        TheoryDocumentBD,
        or_(TheoryDocumentBD.published_version_id.is_(None), TheoryDocumentBD.status != "published"),
    )
    return {
        "content": {
            "tasks": await count(ExamTaskBD, ExamTaskBD.status == "published"),
            "topics": await count(TopicBD, TopicBD.status.in_(("published", "published_manual"))),
            "theoryBlocks": await count(TheoryBlockV2BD),
            "exerciseSets": await count(ExerciseSetBD, ExerciseSetBD.status == "published"),
            "exercises": await count(ExerciseBD, ExerciseBD.status == "published"),
        },
        "activity": {
            "users": await count(UserBD, UserBD.is_active.is_(True)),
            "activeSessions": await count(PracticeSessionBD, PracticeSessionBD.status == "active"),
            "attempts": await count(AttemptV2BD),
        },
        "payments": {
            "mode": settings.payment_mode,
            "configured": settings.payments_enabled,
            "paidOrders": await count(PaymentOrderBD, PaymentOrderBD.status == "paid"),
            "activeSubscriptions": await count(SubscriptionBD, SubscriptionBD.status == "active"),
        },
        "warnings": {
            "emptyExerciseSets": dangling_sets,
            "unpublishedTheoryDocuments": unpublished_docs,
            "adminWithoutToken": not bool(settings.admin_token),
            "internalApiWithoutToken": not bool(settings.backend_internal_token),
        },
    }


def _safe_filename(value: str) -> str:
    return Path(value or "upload").name[:256]


@admin_router.get("/media")
async def list_media(db: AsyncSession = Depends(get_db)):
    assets = list((await db.scalars(
        select(MediaAssetBD)
        .where(MediaAssetBD.status == "active")
        .order_by(MediaAssetBD.created_at.desc())
    )).all())
    return [
        {
            "id": asset.id,
            "publicId": asset.public_id,
            "name": asset.original_name,
            "contentType": asset.content_type,
            "sizeBytes": asset.size_bytes,
            "altText": asset.alt_text,
            "url": f"/api/v2/media/{asset.public_id}",
            "createdAt": asset.created_at,
        }
        for asset in assets
    ]


@admin_router.post("/media", status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content_type = (file.content_type or "").lower()
    extension = ALLOWED_IMAGE_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(415, "Поддерживаются JPG, PNG, WebP и GIF")
    data = await file.read(settings.media_max_bytes + 1)
    if not data:
        raise HTTPException(422, "Файл пуст")
    if len(data) > settings.media_max_bytes:
        raise HTTPException(413, "Файл превышает допустимый размер")
    signatures = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/gif": data.startswith((b"GIF87a", b"GIF89a")),
        "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    }
    if not signatures.get(content_type, False):
        raise HTTPException(422, "Содержимое файла не соответствует его типу")
    public_id = str(uuid.uuid4())
    storage_name = f"{public_id}{extension}"
    settings.media_root.mkdir(parents=True, exist_ok=True)
    path = settings.media_root / storage_name
    path.write_bytes(data)
    asset = MediaAssetBD(
        public_id=public_id,
        original_name=_safe_filename(file.filename or storage_name),
        storage_name=storage_name,
        content_type=content_type,
        size_bytes=len(data),
        alt_text="",
        status="active",
    )
    db.add(asset)
    try:
        await db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {
        "id": asset.id,
        "publicId": asset.public_id,
        "name": asset.original_name,
        "url": f"/api/v2/media/{asset.public_id}",
    }


@admin_router.delete("/media/{asset_id}")
async def archive_media(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await db.get(MediaAssetBD, asset_id)
    if asset is None:
        raise HTTPException(404, "Файл не найден")
    asset.status = "archived"
    await db.commit()
    return {"id": asset.id, "archived": True}


def _set_out(item: ExerciseSetBD, task_number: int, topic_title: str | None, count: int) -> dict[str, Any]:
    configuration = item.configuration or {}
    return {
        "id": item.id,
        "title": item.title,
        "examTaskId": item.exam_task_id,
        "taskNumber": task_number,
        "topicId": item.topic_id,
        "topicTitle": topic_title,
        "status": item.status,
        "accessLevel": item.access_level,
        "selectionStrategy": item.selection_strategy,
        "exerciseCount": count,
        "sessionSize": int(configuration.get("sessionSize", 50)),
        "pageSize": int(configuration.get("pageSize", 5)),
    }


@admin_router.post("/exercise-sets", status_code=201)
async def create_exercise_set(body: ExerciseSetCreateIn, db: AsyncSession = Depends(get_db)):
    task = await db.get(ExamTaskBD, body.exam_task_id)
    if task is None:
        raise HTTPException(404, "Задание не найдено")
    topic = await db.get(TopicBD, body.topic_id) if body.topic_id else None
    topic_link = await db.get(
        ExamTaskTopicBD,
        (task.id, body.topic_id),
    ) if body.topic_id else None
    if body.topic_id and (
        topic is None
        or topic.course_version_id != task.course_version_id
        or topic_link is None
    ):
        raise HTTPException(422, "Тема не принадлежит выбранному заданию")
    if body.page_size > body.session_size:
        raise HTTPException(422, "Размер блока не может превышать размер сессии")
    item = ExerciseSetBD(
        course_version_id=task.course_version_id,
        exam_task_id=task.id,
        topic_id=topic.id if topic else None,
        title=body.title.strip(),
        access_level=body.access_level,
        selection_strategy=body.selection_strategy,
        configuration={
            "scopeRole": "topic" if topic else "task",
            "sessionSize": body.session_size,
            "pageSize": body.page_size,
            "demoSize": 7 if topic else 15,
            "demoSelectionMode": "auto",
        },
        status=body.status,
    )
    db.add(item)
    await db.commit()
    return _set_out(item, task.number, topic.title if topic else None, 0)


@admin_router.put("/exercise-sets/{exercise_set_id}")
async def update_exercise_set(
    exercise_set_id: int,
    body: ExerciseSetUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(ExerciseSetBD, exercise_set_id)
    if item is None:
        raise HTTPException(404, "Подборка не найдена")
    topic = await db.get(TopicBD, body.topic_id) if body.topic_id else None
    topic_link = await db.get(
        ExamTaskTopicBD,
        (item.exam_task_id, body.topic_id),
    ) if body.topic_id else None
    if body.topic_id and (
        topic is None
        or topic.course_version_id != item.course_version_id
        or topic_link is None
    ):
        raise HTTPException(422, "Тема не принадлежит заданию подборки")
    item.title = body.title.strip()
    item.topic_id = topic.id if topic else None
    item.status = body.status
    item.access_level = body.access_level
    item.selection_strategy = body.selection_strategy
    item.configuration = {
        **(item.configuration or {}),
        "scopeRole": "topic" if topic else "task",
    }
    await db.commit()
    task = await db.get(ExamTaskBD, item.exam_task_id)
    count = int(await db.scalar(select(func.count()).select_from(ExerciseSetItemBD).where(
        ExerciseSetItemBD.exercise_set_id == item.id
    )) or 0)
    return _set_out(item, task.number, topic.title if topic else None, count)


@admin_router.delete("/exercise-sets/{exercise_set_id}")
async def archive_exercise_set(exercise_set_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ExerciseSetBD, exercise_set_id)
    if item is None:
        raise HTTPException(404, "Подборка не найдена")
    item.status = "archived"
    await db.commit()
    return {"id": item.id, "archived": True}


def _exercise_out(
    item: ExerciseSetItemBD,
    exercise: ExerciseBD,
    version: ExerciseVersionBD,
    task_ids: list[int] | None = None,
    topic_ids: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "exerciseId": exercise.id,
        "setItemId": item.id,
        "sortOrder": item.sort_order,
        "isPreview": item.is_preview,
        "status": exercise.status,
        "difficulty": exercise.difficulty,
        "source": exercise.source,
        "version": version.version_number,
        "interactionType": version.interaction_type,
        "promptData": version.prompt_data,
        "interactionConfig": version.interaction_config,
        "answerConfig": version.answer_config,
        "checkerType": version.checker_type,
        "checkerConfig": version.checker_config,
        "feedbackData": version.feedback_data,
        "examTaskIds": task_ids or [],
        "topicIds": topic_ids or [],
    }


@admin_router.get("/exercise-sets/{exercise_set_id}/items")
async def list_exercise_items(
    exercise_set_id: int,
    search: str = Query(default="", max_length=200),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    if await db.get(ExerciseSetBD, exercise_set_id) is None:
        raise HTTPException(404, "Подборка не найдена")
    base = (
        select(ExerciseSetItemBD, ExerciseBD, ExerciseVersionBD)
        .join(ExerciseBD, ExerciseBD.id == ExerciseSetItemBD.exercise_id)
        .join(ExerciseVersionBD, ExerciseVersionBD.id == ExerciseBD.published_version_id)
        .where(ExerciseSetItemBD.exercise_set_id == exercise_set_id)
    )
    if search.strip():
        needle = f"%{search.strip().lower()}%"
        base = base.where(func.lower(func.cast(ExerciseVersionBD.prompt_data, String)).like(needle))
    total = int(await db.scalar(select(func.count()).select_from(base.subquery())) or 0)
    rows = (await db.execute(
        base.order_by(ExerciseSetItemBD.sort_order, ExerciseSetItemBD.id).offset(offset).limit(limit)
    )).all()
    exercise_ids = [exercise.id for _, exercise, _ in rows]
    task_links: dict[int, list[int]] = {}
    topic_links: dict[int, list[int]] = {}
    if exercise_ids:
        for exercise_id, task_id in (await db.execute(select(
            ExerciseTaskLinkBD.exercise_id,
            ExerciseTaskLinkBD.exam_task_id,
        ).where(ExerciseTaskLinkBD.exercise_id.in_(exercise_ids)))).all():
            task_links.setdefault(exercise_id, []).append(task_id)
        for exercise_id, topic_id in (await db.execute(select(
            ExerciseTopicLinkBD.exercise_id,
            ExerciseTopicLinkBD.topic_id,
        ).where(ExerciseTopicLinkBD.exercise_id.in_(exercise_ids)))).all():
            topic_links.setdefault(exercise_id, []).append(topic_id)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            _exercise_out(*row, task_links.get(row[1].id), topic_links.get(row[1].id))
            for row in rows
        ],
    }


def _validate_exercise(body: ExerciseVersionIn) -> None:
    if body.interaction_type not in ALLOWED_INTERACTIONS:
        raise HTTPException(422, "Неизвестный тип взаимодействия")
    if not body.prompt_data:
        raise HTTPException(422, "У упражнения нет условия")
    if not body.answer_config:
        raise HTTPException(422, "У упражнения нет правильного ответа")
    if body.interaction_type in {"single_choice", "multiple_choice"}:
        options = body.interaction_config.get("options") or []
        keys = {str(option.get("key")) for option in options if option.get("key")}
        if len(keys) < 2:
            raise HTTPException(422, "Для выбора нужны хотя бы два разных варианта")
        correct = (
            {str(body.answer_config.get("correctOptionKey"))}
            if body.interaction_type == "single_choice"
            else {str(value) for value in body.answer_config.get("correctOptionKeys", [])}
        )
        if not correct or not correct.issubset(keys):
            raise HTTPException(422, "Правильный вариант отсутствует в списке")
    elif body.interaction_type == "stress_selection":
        position = body.answer_config.get("correctCharacterIndex")
        content = str(body.prompt_data.get("content") or body.prompt_data.get("word") or "")
        if not isinstance(position, int) or position < 0 or position >= len(content):
            raise HTTPException(422, "Позиция ударения выходит за границы слова")
    else:
        accepted = [str(value).strip() for value in body.answer_config.get("acceptedAnswers", [])]
        if not any(accepted):
            raise HTTPException(422, "Добавьте хотя бы один непустой правильный ответ")


def _correct_answer_label(body: ExerciseVersionIn) -> str:
    if body.interaction_type in {"single_choice", "multiple_choice"}:
        labels = {
            str(option.get("key")): str(option.get("label") or "")
            for option in body.interaction_config.get("options", [])
        }
        keys = (
            [body.answer_config.get("correctOptionKey")]
            if body.interaction_type == "single_choice"
            else body.answer_config.get("correctOptionKeys", [])
        )
        return ", ".join(labels.get(str(key), str(key)) for key in keys)
    if body.interaction_type == "stress_selection":
        word = str(body.prompt_data.get("content") or body.prompt_data.get("word") or "")
        position = int(body.answer_config.get("correctCharacterIndex", 0))
        return "".join(character.upper() if index == position else character for index, character in enumerate(word))
    return str((body.answer_config.get("acceptedAnswers") or [""])[0])


@admin_router.put("/exercise-sets/{exercise_set_id}/items/{exercise_id}")
async def update_exercise(
    exercise_set_id: int,
    exercise_id: int,
    body: ExerciseVersionIn,
    db: AsyncSession = Depends(get_db),
):
    _validate_exercise(body)
    membership = await db.scalar(select(ExerciseSetItemBD).where(
        ExerciseSetItemBD.exercise_set_id == exercise_set_id,
        ExerciseSetItemBD.exercise_id == exercise_id,
    ))
    exercise = await db.get(ExerciseBD, exercise_id)
    if membership is None or exercise is None:
        raise HTTPException(404, "Упражнение не найдено в подборке")
    next_number = int(await db.scalar(select(func.max(ExerciseVersionBD.version_number)).where(
        ExerciseVersionBD.exercise_id == exercise.id
    )) or 0) + 1
    now = datetime.now(timezone.utc)
    feedback_data = {
        **body.feedback_data,
        "correctAnswer": _correct_answer_label(body),
    }
    version = ExerciseVersionBD(
        exercise_id=exercise.id,
        version_number=next_number,
        status="published",
        interaction_type=body.interaction_type,
        response_schema_version=1,
        prompt_data=body.prompt_data,
        interaction_config=body.interaction_config,
        answer_config=body.answer_config,
        checker_type=body.checker_type,
        checker_config=body.checker_config,
        feedback_data=feedback_data,
        published_at=now,
    )
    db.add(version)
    await db.flush()
    old_version = await db.get(ExerciseVersionBD, exercise.published_version_id)
    if old_version:
        old_version.status = "archived"
    exercise.published_version_id = version.id
    exercise.status = "published"
    exercise.difficulty = body.difficulty
    exercise.source = body.source
    if body.exam_task_ids is not None:
        valid_task_ids = set((await db.scalars(select(ExamTaskBD.id).where(
            ExamTaskBD.course_version_id == exercise.course_version_id,
            ExamTaskBD.id.in_(set(body.exam_task_ids)),
        ))).all())
        if valid_task_ids != set(body.exam_task_ids):
            raise HTTPException(422, "Одно из заданий относится к другой версии курса")
        await db.execute(delete(ExerciseTaskLinkBD).where(ExerciseTaskLinkBD.exercise_id == exercise.id))
        for index, task_id in enumerate(body.exam_task_ids):
            db.add(ExerciseTaskLinkBD(exercise_id=exercise.id, exam_task_id=task_id, is_primary=index == 0))
    if body.topic_ids is not None:
        valid_topic_ids = set((await db.scalars(select(TopicBD.id).where(
            TopicBD.course_version_id == exercise.course_version_id,
            TopicBD.id.in_(set(body.topic_ids)),
        ))).all())
        if valid_topic_ids != set(body.topic_ids):
            raise HTTPException(422, "Одна из тем относится к другой версии курса")
        await db.execute(delete(ExerciseTopicLinkBD).where(ExerciseTopicLinkBD.exercise_id == exercise.id))
        for index, topic_id in enumerate(body.topic_ids):
            db.add(ExerciseTopicLinkBD(exercise_id=exercise.id, topic_id=topic_id, is_primary=index == 0))
    await db.commit()
    return _exercise_out(
        membership,
        exercise,
        version,
        body.exam_task_ids,
        body.topic_ids,
    )


@admin_router.delete("/exercise-sets/{exercise_set_id}/items/{exercise_id}")
async def remove_exercise_from_set(
    exercise_set_id: int,
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
):
    membership = await db.scalar(select(ExerciseSetItemBD).where(
        ExerciseSetItemBD.exercise_set_id == exercise_set_id,
        ExerciseSetItemBD.exercise_id == exercise_id,
    ))
    if membership is None:
        raise HTTPException(404, "Упражнение не найдено в подборке")
    await db.delete(membership)
    await db.flush()
    other_count = int(await db.scalar(select(func.count()).select_from(ExerciseSetItemBD).where(
        ExerciseSetItemBD.exercise_id == exercise_id
    )) or 0)
    if other_count == 0:
        exercise = await db.get(ExerciseBD, exercise_id)
        if exercise:
            exercise.status = "archived"
    await db.commit()
    return {"exerciseId": exercise_id, "removed": True, "archived": other_count == 0}


@admin_router.get("/users")
async def list_users(
    search: str = Query(default="", max_length=200),
    limit: int = Query(default=100, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
):
    query = select(UserBD).order_by(UserBD.last_active_at.desc().nullslast(), UserBD.id.desc()).limit(limit)
    if search.strip():
        needle = f"%{search.strip().lower()}%"
        query = query.where(or_(
            func.lower(UserBD.name).like(needle),
            func.lower(UserBD.username).like(needle),
            UserBD.tg_id.like(f"%{search.strip()}%"),
        ))
    users = list((await db.scalars(query)).all())
    result = []
    for user in users:
        active_access = int(await db.scalar(select(func.count()).select_from(EntitlementBD).where(
            EntitlementBD.user_id == user.id,
            EntitlementBD.status == "active",
            or_(EntitlementBD.ends_at.is_(None), EntitlementBD.ends_at > datetime.now(timezone.utc)),
        )) or 0)
        result.append({
            "id": user.id,
            "telegramId": user.tg_id,
            "name": " ".join(part for part in (user.name, user.second_name) if part),
            "username": user.username,
            "isActive": user.is_active,
            "lastActiveAt": user.last_active_at,
            "activeAccessCount": active_access,
        })
    return result


@admin_router.get("/payments")
async def payment_operations(db: AsyncSession = Depends(get_db)):
    orders = (await db.execute(
        select(PaymentOrderBD, ProductBD.title, UserBD.tg_id)
        .join(ProductBD, ProductBD.id == PaymentOrderBD.product_id)
        .join(UserBD, UserBD.id == PaymentOrderBD.user_id)
        .order_by(PaymentOrderBD.created_at.desc())
        .limit(200)
    )).all()
    grants = (await db.execute(
        select(EntitlementBD, AccessPolicyBD.title, UserBD.tg_id)
        .join(AccessPolicyBD, AccessPolicyBD.id == EntitlementBD.access_policy_id)
        .join(UserBD, UserBD.id == EntitlementBD.user_id)
        .order_by(EntitlementBD.created_at.desc())
        .limit(300)
    )).all()
    return {
        "orders": [{
            "id": order.id,
            "publicId": order.public_id,
            "userId": order.user_id,
            "telegramId": tg_id,
            "productTitle": title,
            "amount": order.amount,
            "currency": order.currency,
            "status": order.status,
            "createdAt": order.created_at,
            "paidAt": order.paid_at,
        } for order, title, tg_id in orders],
        "entitlements": [{
            "id": entitlement.id,
            "userId": entitlement.user_id,
            "telegramId": tg_id,
            "title": title,
            "status": entitlement.status,
            "sourceType": entitlement.source_type,
            "sourceNote": entitlement.source_note,
            "startsAt": entitlement.starts_at,
            "endsAt": entitlement.ends_at,
        } for entitlement, title, tg_id in grants],
    }


@admin_router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    body: UserStatusIn,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(UserBD, user_id)
    if user is None:
        raise HTTPException(404, "Пользователь не найден")
    user.is_active = body.is_active
    await db.commit()
    return {"id": user.id, "isActive": user.is_active}


@admin_router.post("/entitlements", status_code=201)
async def grant_entitlement(body: ManualGrantIn, db: AsyncSession = Depends(get_db)):
    user = await db.get(UserBD, body.user_id)
    product = await db.get(ProductBD, body.product_id)
    if user is None or product is None:
        raise HTTPException(404, "Пользователь или продукт не найден")
    now = datetime.now(timezone.utc)
    entitlement = await db.scalar(select(EntitlementBD).where(
        EntitlementBD.user_id == user.id,
        EntitlementBD.access_policy_id == product.access_policy_id,
        EntitlementBD.source_type == "manual",
        EntitlementBD.status == "active",
    ).order_by(EntitlementBD.id.desc()))
    if entitlement is None:
        entitlement = EntitlementBD(
            user_id=user.id,
            access_policy_id=product.access_policy_id,
            source_order_id=None,
            source_type="manual",
            source_note=body.note.strip(),
            status="active",
            starts_at=now,
            ends_at=body.ends_at,
        )
        db.add(entitlement)
    else:
        entitlement.ends_at = body.ends_at
        entitlement.source_note = body.note.strip()
    await db.commit()
    return {"id": entitlement.id, "status": entitlement.status}


@admin_router.post("/entitlements/{entitlement_id}/revoke")
async def revoke_entitlement(entitlement_id: int, db: AsyncSession = Depends(get_db)):
    entitlement = await db.get(EntitlementBD, entitlement_id)
    if entitlement is None:
        raise HTTPException(404, "Доступ не найден")
    entitlement.status = "revoked"
    await db.commit()
    return {"id": entitlement.id, "status": entitlement.status}


@admin_router.get("/audit")
async def audit_log(limit: int = Query(default=100, ge=1, le=500), db: AsyncSession = Depends(get_db)):
    entries = list((await db.scalars(
        select(AdminAuditLogBD).order_by(AdminAuditLogBD.created_at.desc()).limit(limit)
    )).all())
    return [{
        "id": item.id,
        "method": item.method,
        "path": item.path,
        "statusCode": item.status_code,
        "remoteAddress": item.remote_address,
        "createdAt": item.created_at,
    } for item in entries]
