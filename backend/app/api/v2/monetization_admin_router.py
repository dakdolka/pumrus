from __future__ import annotations

import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.admin_router import require_admin
from app.core.db import get_db
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, TopicBD
from app.infra.exercises.models import ExerciseSetBD
from app.infra.monetization.models import (
    AccessPolicyBD,
    AccessPolicyResourceBD,
    PriceBD,
    ProductBD,
)


router = APIRouter(
    prefix="/v2/admin/monetization",
    tags=["v2-admin-monetization"],
    dependencies=[Depends(require_admin)],
)


class ProductResourceIn(BaseModel):
    resource_type: Literal["course_version", "exam_task", "topic", "exercise_set"]
    resource_id: int


class ProductIn(BaseModel):
    code: str = Field(min_length=2, max_length=96)
    title: str = Field(min_length=1, max_length=256)
    description: str = Field(default="", max_length=2000)
    billing_type: Literal["one_time", "monthly"] = "one_time"
    status: Literal["draft", "active", "archived"] = "draft"
    amount: int = Field(ge=100, le=10_000_000)
    resources: list[ProductResourceIn] = Field(default_factory=list, max_length=500)


def _normalized_code(value: str) -> str:
    code = re.sub(r"[^a-z0-9_-]+", "-", value.casefold()).strip("-")
    if len(code) < 2:
        raise HTTPException(422, "Код должен содержать латинские буквы или цифры")
    return code[:96]


async def _product_out(db: AsyncSession, product: ProductBD) -> dict:
    price = await db.scalar(select(PriceBD).where(
        PriceBD.product_id == product.id,
        PriceBD.provider == "yookassa",
    ))
    resources = list((await db.scalars(select(AccessPolicyResourceBD).where(
        AccessPolicyResourceBD.access_policy_id == product.access_policy_id,
    ).order_by(
        AccessPolicyResourceBD.resource_type,
        AccessPolicyResourceBD.resource_id,
    ))).all())
    return {
        "id": product.id,
        "code": product.code,
        "title": product.title,
        "description": product.description,
        "billingType": product.billing_type,
        "status": product.status,
        "amount": price.amount if price else 1,
        "priceId": price.id if price else None,
        "provider": "yookassa",
        "currency": "RUB",
        "resources": [
            {"resourceType": item.resource_type, "resourceId": item.resource_id}
            for item in resources
        ],
    }


@router.get("/products")
async def list_products(db: AsyncSession = Depends(get_db)):
    products = list((await db.scalars(
        select(ProductBD).order_by(ProductBD.status, ProductBD.id)
    )).all())
    return [await _product_out(db, item) for item in products]


@router.get("/resources")
async def list_resources(db: AsyncSession = Depends(get_db)):
    course_versions = list((await db.scalars(
        select(CourseVersionBD).order_by(CourseVersionBD.id)
    )).all())
    tasks = list((await db.scalars(
        select(ExamTaskBD).order_by(ExamTaskBD.number)
    )).all())
    topics = list((await db.scalars(
        select(TopicBD).order_by(TopicBD.title)
    )).all())
    exercise_sets = list((await db.scalars(
        select(ExerciseSetBD)
        .where(ExerciseSetBD.status == "published")
        .order_by(ExerciseSetBD.exam_task_id, ExerciseSetBD.title)
    )).all())
    task_numbers = {item.id: item.number for item in tasks}
    return [
        *[
            {
                "resourceType": "course_version",
                "resourceId": item.id,
                "group": "Весь курс",
                "label": item.title,
            }
            for item in course_versions
        ],
        *[
            {
                "resourceType": "exam_task",
                "resourceId": item.id,
                "group": "Задания",
                "label": f"Задание {item.number}: {item.title}",
            }
            for item in tasks
        ],
        *[
            {
                "resourceType": "topic",
                "resourceId": item.id,
                "group": "Темы",
                "label": item.title,
            }
            for item in topics
        ],
        *[
            {
                "resourceType": "exercise_set",
                "resourceId": item.id,
                "group": "Тренажёры",
                "label": f"Задание {task_numbers.get(item.exam_task_id, '—')}: {item.title}",
            }
            for item in exercise_sets
        ],
    ]


async def _save_product(
    db: AsyncSession,
    body: ProductIn,
    product: ProductBD | None = None,
) -> ProductBD:
    if body.status == "active" and not body.resources:
        raise HTTPException(
            422,
            "Опубликованный продукт должен открывать хотя бы один элемент курса",
        )
    resource_models = {
        "course_version": CourseVersionBD,
        "exam_task": ExamTaskBD,
        "topic": TopicBD,
        "exercise_set": ExerciseSetBD,
    }
    for resource_type, model in resource_models.items():
        requested = {
            resource.resource_id
            for resource in body.resources
            if resource.resource_type == resource_type
        }
        if not requested:
            continue
        existing = set((await db.scalars(select(model.id).where(model.id.in_(requested)))).all())
        missing = sorted(requested - existing)
        if missing:
            raise HTTPException(
                422,
                f"Не найдены элементы доступа {resource_type}: {missing}",
            )
    code = _normalized_code(body.code)
    duplicate = await db.scalar(select(ProductBD.id).where(
        ProductBD.code == code,
        ProductBD.id != (product.id if product else -1),
    ))
    if duplicate is not None:
        raise HTTPException(409, "Продукт с таким кодом уже существует")
    if product is None:
        policy = AccessPolicyBD(
            code=f"product-{uuid.uuid4().hex[:20]}",
            title=body.title,
        )
        db.add(policy)
        await db.flush()
        product = ProductBD(
            code=code,
            title=body.title,
            description=body.description,
            billing_type=body.billing_type,
            status=body.status,
            access_policy_id=policy.id,
        )
        db.add(product)
        await db.flush()
        price = PriceBD(
            product_id=product.id,
            provider="yookassa",
            currency="RUB",
            amount=body.amount,
            status="active",
        )
        db.add(price)
    else:
        product.code = code
        product.title = body.title
        product.description = body.description
        product.billing_type = body.billing_type
        product.status = body.status
        policy = await db.get(AccessPolicyBD, product.access_policy_id)
        if policy:
            policy.title = body.title
        price = await db.scalar(select(PriceBD).where(
            PriceBD.product_id == product.id,
            PriceBD.provider == "yookassa",
        ))
        if price is None:
            price = PriceBD(
                product_id=product.id,
                provider="yookassa",
                currency="RUB",
                amount=body.amount,
                status="active",
            )
            db.add(price)
        else:
            price.amount = body.amount
            price.status = "active"
        await db.execute(delete(AccessPolicyResourceBD).where(
            AccessPolicyResourceBD.access_policy_id == product.access_policy_id
        ))
    seen_resources: set[tuple[str, int]] = set()
    for resource in body.resources:
        resource_key = (resource.resource_type, resource.resource_id)
        if resource_key in seen_resources:
            continue
        seen_resources.add(resource_key)
        db.add(AccessPolicyResourceBD(
            access_policy_id=product.access_policy_id,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
        ))
    await db.commit()
    return product


@router.post("/products", status_code=201)
async def create_product(body: ProductIn, db: AsyncSession = Depends(get_db)):
    product = await _save_product(db, body)
    return await _product_out(db, product)


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    body: ProductIn,
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(ProductBD, product_id)
    if product is None:
        raise HTTPException(404, "Продукт не найден")
    product = await _save_product(db, body, product)
    return await _product_out(db, product)
