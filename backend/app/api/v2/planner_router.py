from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.internal_router import require_internal
from app.core.db import get_db
from app.core.monetization import telegram_user_from_request
from app.core.planner import advance_delivery, checked_zone, clear_lease, next_weekly, plan_dates
from app.infra.catalog.models import CourseVersionBD, ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.infra.planner.models import StudyPlanBD, StudyReminderBD
from app.infra.user.general.models import UserBD

router = APIRouter(prefix="/v2/planner", tags=["v2-planner"])
internal_router = APIRouter(prefix="/v2/internal/reminders", tags=["v2-internal"],
                           dependencies=[Depends(require_internal)])


class CalendarIn(BaseModel):
    timezone: str = Field(min_length=1, max_length=64)
    local_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    weekdays: list[int] = Field(default_factory=list, max_length=7)

    @field_validator("timezone")
    @classmethod
    def validate_zone(cls, value):
        checked_zone(value)
        return value

    @field_validator("weekdays")
    @classmethod
    def validate_days(cls, value):
        if any(day not in range(7) for day in value):
            raise ValueError("Дни недели должны быть от 0 (пн) до 6 (вс)")
        return sorted(set(value))


class TargetIn(BaseModel):
    activity: Literal["theory", "practice", "mistakes", "custom"] = "theory"
    task_number: int | None = Field(default=None, ge=1, le=99)
    topic_id: int | None = Field(default=None, gt=0)


class ReminderIn(CalendarIn, TargetIn):
    request_key: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    due_at: AwareDatetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Введите название напоминания")
        return value.strip()


class PlanIn(CalendarIn):
    weekdays: list[int] = Field(min_length=1, max_length=7)
    request_key: str = Field(min_length=1, max_length=64)
    title: str = Field(default="Мой план подготовки", min_length=1, max_length=160)
    task_numbers: list[int] = Field(min_length=1, max_length=99)
    activity: Literal["theory", "practice", "mixed"] = "mixed"
    start_date: date
    end_by: date | None = None

    @field_validator("weekdays")
    @classmethod
    def require_days(cls, value):
        if not value:
            raise ValueError("Выберите учебные дни")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Введите название плана")
        return value.strip()


class ActionIn(BaseModel):
    action: Literal["complete", "pause", "resume", "snooze"]
    minutes: int = Field(default=60, ge=5, le=10080)


class PlanActionIn(BaseModel):
    action: Literal["pause", "resume"]


class RescheduleIn(CalendarIn):
    weekdays: list[int] = Field(min_length=1, max_length=7)
    start_date: date


async def planner_user(request: Request, db: AsyncSession = Depends(get_db)) -> UserBD:
    if not request.headers.get("X-Telegram-Init-Data"):
        raise HTTPException(401, "Откройте план занятий из Telegram")
    user = await telegram_user_from_request(request, db, required=True)
    if not user.is_active:
        raise HTTPException(403, "Аккаунт недоступен")
    # Serialize user mutations, including creation limits and idempotent requests.
    if request.method != "GET":
        await db.scalar(select(UserBD.id).where(UserBD.id == user.id).with_for_update())
    return user


def reminder_out(item):
    return {
        "id": item.id, "planId": item.plan_id, "title": item.title,
        "targetPath": item.target_path, "timezone": item.timezone,
        "weekdays": item.weekdays, "localTime": item.local_time,
        "status": item.status, "dueAt": item.due_at,
        "nextNotifyAt": item.next_notify_at, "lastSentAt": item.last_sent_at,
        "deliveryStatus": item.delivery_status, "completedAt": item.completed_at,
    }


async def owned_reminder(db, user_id, reminder_id):
    item = await db.scalar(select(StudyReminderBD).where(
        StudyReminderBD.id == reminder_id, StudyReminderBD.user_id == user_id,
    ).with_for_update())
    if item is None:
        raise HTTPException(404, "Напоминание не найдено")
    return item


async def owned_plan(db, user_id, plan_id):
    plan = await db.scalar(select(StudyPlanBD).where(
        StudyPlanBD.id == plan_id, StudyPlanBD.user_id == user_id,
    ).with_for_update())
    if plan is None:
        raise HTTPException(404, "План не найден")
    return plan


async def target_path(db, body: TargetIn):
    if body.activity in ("custom", "mistakes"):
        if body.task_number or body.topic_id:
            raise HTTPException(422, "Для этого типа не нужно выбирать задание или тему")
        return "/planner" if body.activity == "custom" else "/practice/mistakes"
    if body.task_number is None:
        raise HTTPException(422, "Выберите задание")
    task = await db.scalar(select(ExamTaskBD).join(CourseVersionBD).where(
        ExamTaskBD.number == body.task_number, ExamTaskBD.status == "published",
        CourseVersionBD.is_active.is_(True),
    ))
    if task is None:
        raise HTTPException(422, "Задание недоступно")
    path = f"/{body.activity}/tasks/{task.number}"
    if body.topic_id is not None:
        topic = await db.scalar(select(TopicBD).join(ExamTaskTopicBD).where(
            ExamTaskTopicBD.exam_task_id == task.id, TopicBD.id == body.topic_id,
            TopicBD.status.in_(("published", "published_manual")),
        ))
        if topic is None:
            raise HTTPException(422, "Тема не относится к выбранному заданию")
        path += (f"/topics/{topic.id}" if body.activity == "theory" else f"?topic={topic.id}")
    return path


async def ensure_capacity(db, user_id, additional):
    count = await db.scalar(select(func.count()).select_from(StudyReminderBD).where(
        StudyReminderBD.user_id == user_id, StudyReminderBD.status != "completed",
    ))
    if count + additional > 1000:
        raise HTTPException(409, "Можно запланировать до 1000 незавершённых занятий")


def future_due(body: ReminderIn, now: datetime):
    due = body.due_at.astimezone(timezone.utc)
    if due <= now or due > now + timedelta(days=2200):
        raise HTTPException(422, "Выберите будущую дату в пределах шести лет")
    if body.weekdays:
        expected = next_weekly(due - timedelta(seconds=1), body.weekdays,
                               body.local_time, body.timezone)
        if abs((expected - due).total_seconds()) > 1:
            raise HTTPException(422, "Дата и время должны совпадать с расписанием повторений")
    return due


@router.get("")
async def overview(user: UserBD = Depends(planner_user), db: AsyncSession = Depends(get_db)):
    plans = (await db.scalars(select(StudyPlanBD).where(StudyPlanBD.user_id == user.id)
                             .order_by(StudyPlanBD.created_at.desc()))).all()
    # Completed history is bounded; all pending items remain visible.
    items = list((await db.scalars(select(StudyReminderBD).where(
        StudyReminderBD.user_id == user.id, StudyReminderBD.status != "completed",
    ).order_by(StudyReminderBD.due_at, StudyReminderBD.id))).all())
    items += list((await db.scalars(select(StudyReminderBD).where(
        StudyReminderBD.user_id == user.id, StudyReminderBD.status == "completed",
    ).order_by(StudyReminderBD.completed_at.desc()).limit(100))).all())
    counts = (await db.execute(select(StudyReminderBD.plan_id, StudyReminderBD.status, func.count())
                              .where(StudyReminderBD.user_id == user.id)
                              .group_by(StudyReminderBD.plan_id, StudyReminderBD.status))).all()
    totals = {}
    for plan_id, status, count in counts:
        stats = totals.setdefault(plan_id, {"total": 0, "completed": 0})
        stats["total"] += count
        if status == "completed":
            stats["completed"] += count
    return {"serverNow": datetime.now(timezone.utc), "reminders": [reminder_out(i) for i in items],
            "plans": [{"id": p.id, "title": p.title, "status": p.status, "schedule": p.schedule,
                       **totals.get(p.id, {"total": 0, "completed": 0})} for p in plans]}


@router.post("/reminders", status_code=201)
async def create_reminder(body: ReminderIn, user: UserBD = Depends(planner_user),
                          db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(StudyReminderBD).where(
        StudyReminderBD.user_id == user.id, StudyReminderBD.request_key == body.request_key))
    if existing:
        return reminder_out(existing)
    due = future_due(body, datetime.now(timezone.utc))
    path = await target_path(db, body)
    await ensure_capacity(db, user.id, 1)
    item = StudyReminderBD(user_id=user.id, request_key=body.request_key, title=body.title,
                           target_path=path, timezone=body.timezone, weekdays=body.weekdays,
                           local_time=body.local_time, due_at=due, next_notify_at=due)
    db.add(item)
    await db.commit()
    return reminder_out(item)


@router.put("/reminders/{reminder_id}")
async def edit_reminder(reminder_id: int, body: ReminderIn, user: UserBD = Depends(planner_user),
                        db: AsyncSession = Depends(get_db)):
    due = future_due(body, datetime.now(timezone.utc))
    path = await target_path(db, body)
    item = await owned_reminder(db, user.id, reminder_id)
    if item.status == "completed":
        raise HTTPException(409, "Завершённое занятие нельзя редактировать")
    if item.plan_id and body.weekdays:
        raise HTTPException(422, "Занятие плана не может повторяться")
    item.title, item.target_path = body.title, path
    item.timezone, item.local_time, item.weekdays = body.timezone, body.local_time, body.weekdays
    item.due_at = item.next_notify_at = due
    item.delivery_status, item.attempts = "pending", 0
    clear_lease(item)
    await db.commit()
    return reminder_out(item)


@router.post("/reminders/{reminder_id}/actions")
async def reminder_action(reminder_id: int, body: ActionIn, user: UserBD = Depends(planner_user),
                          db: AsyncSession = Depends(get_db)):
    item = await owned_reminder(db, user.id, reminder_id)
    now = datetime.now(timezone.utc)
    if item.status == "completed":
        if body.action == "complete":
            return reminder_out(item)
        raise HTTPException(409, "Это занятие уже завершено")
    clear_lease(item)
    if body.action == "complete":
        item.status, item.completed_at, item.next_notify_at = "completed", now, None
    elif body.action == "pause":
        item.status = "paused"
    else:
        item.status, item.delivery_status, item.attempts = "active", "pending", 0
        if body.action == "snooze":
            item.next_notify_at = now + timedelta(minutes=body.minutes)
            if not item.weekdays:
                item.due_at = item.next_notify_at
        elif item.weekdays:
            item.due_at = item.next_notify_at = next_weekly(now, item.weekdays, item.local_time, item.timezone)
        else:
            item.due_at = item.next_notify_at = max(item.due_at, now + timedelta(minutes=5))
    await db.commit()
    return reminder_out(item)


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, user: UserBD = Depends(planner_user),
                          db: AsyncSession = Depends(get_db)):
    await db.delete(await owned_reminder(db, user.id, reminder_id))
    await db.commit()
    return {"ok": True}


async def build_plan(db, body: PlanIn):
    numbers = sorted(set(body.task_numbers))
    tasks = (await db.scalars(select(ExamTaskBD).join(CourseVersionBD).where(
        ExamTaskBD.number.in_(numbers), ExamTaskBD.status == "published",
        CourseVersionBD.is_active.is_(True),
    ).order_by(ExamTaskBD.sort_order, ExamTaskBD.number))).all()
    if len(tasks) != len(numbers):
        raise HTTPException(422, "Часть выбранных заданий недоступна")
    units = []
    modes = ("theory", "practice") if body.activity == "mixed" else (body.activity,)
    for task in tasks:
        for mode in modes:
            label = "Теория" if mode == "theory" else "Практика"
            units.append((f"{label} · задание {task.number}: {task.title}"[:160], f"/{mode}/tasks/{task.number}"))
    try:
        dates = plan_dates(body.start_date, len(units), body.weekdays, body.local_time,
                           body.timezone, datetime.now(timezone.utc))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if body.end_by and dates[-1].astimezone(checked_zone(body.timezone)).date() > body.end_by:
        raise HTTPException(422, "План не укладывается в срок. Добавьте учебные дни или сократите задания")
    return [{"title": title, "targetPath": path, "dueAt": due}
            for (title, path), due in zip(units, dates)]


@router.post("/plans/preview")
async def preview_plan(body: PlanIn, user: UserBD = Depends(planner_user),
                       db: AsyncSession = Depends(get_db)):
    return {"items": await build_plan(db, body)}


@router.post("/plans", status_code=201)
async def create_plan(body: PlanIn, user: UserBD = Depends(planner_user),
                      db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(StudyPlanBD).where(
        StudyPlanBD.user_id == user.id, StudyPlanBD.request_key == body.request_key))
    if existing:
        return {"id": existing.id}
    plan_count = await db.scalar(select(func.count()).select_from(StudyPlanBD).where(StudyPlanBD.user_id == user.id))
    if plan_count >= 10:
        raise HTTPException(409, "Можно создать до 10 планов. Удалите ненужный план")
    units = await build_plan(db, body)
    await ensure_capacity(db, user.id, len(units))
    plan = StudyPlanBD(user_id=user.id, request_key=body.request_key, title=body.title,
                       schedule=body.model_dump(mode="json", exclude={"request_key", "title"}))
    db.add(plan)
    await db.flush()
    for unit in units:
        db.add(StudyReminderBD(user_id=user.id, plan_id=plan.id, title=unit["title"],
                               target_path=unit["targetPath"], timezone=body.timezone, weekdays=[],
                               local_time=body.local_time, due_at=unit["dueAt"], next_notify_at=unit["dueAt"]))
    await db.commit()
    return {"id": plan.id}


@router.post("/plans/{plan_id}/actions")
async def plan_action(plan_id: int, body: PlanActionIn, user: UserBD = Depends(planner_user),
                      db: AsyncSession = Depends(get_db)):
    plan = await owned_plan(db, user.id, plan_id)
    plan.status = "paused" if body.action == "pause" else "active"
    items = (await db.scalars(select(StudyReminderBD).where(StudyReminderBD.plan_id == plan.id)
                             .with_for_update())).all()
    for item in items:
        clear_lease(item)
    # Resume preserves dates: overdue lessons stay visible without replaying old notifications.
    await db.commit()
    return {"ok": True}


@router.post("/plans/{plan_id}/reschedule")
async def reschedule_plan(plan_id: int, body: RescheduleIn, user: UserBD = Depends(planner_user),
                          db: AsyncSession = Depends(get_db)):
    plan = await owned_plan(db, user.id, plan_id)
    if not body.weekdays:
        raise HTTPException(422, "Выберите учебные дни")
    items = (await db.scalars(select(StudyReminderBD).where(
        StudyReminderBD.plan_id == plan.id, StudyReminderBD.status != "completed",
    ).order_by(StudyReminderBD.id).with_for_update())).all()
    if not items:
        raise HTTPException(409, "Все занятия плана уже завершены")
    try:
        dates = plan_dates(body.start_date, len(items), body.weekdays, body.local_time,
                           body.timezone, datetime.now(timezone.utc))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    for item, due in zip(items, dates):
        item.due_at = item.next_notify_at = due
        item.timezone, item.local_time = body.timezone, body.local_time
        item.delivery_status, item.attempts = "pending", 0
        clear_lease(item)
    plan.schedule = {**plan.schedule, **body.model_dump(mode="json"), "end_by": None}
    await db.commit()
    return {"ok": True}


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, user: UserBD = Depends(planner_user),
                      db: AsyncSession = Depends(get_db)):
    await db.delete(await owned_plan(db, user.id, plan_id))
    await db.commit()
    return {"ok": True}


class ReceiptIn(BaseModel):
    token: str = Field(min_length=36, max_length=36)
    outcome: Literal["sent", "retry", "blocked", "failed"]
    retry_after: int | None = Field(default=None, ge=1, le=86400)


@internal_router.post("/claim")
async def claim_reminders(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(StudyReminderBD, UserBD.tg_id)
        .join(UserBD, UserBD.id == StudyReminderBD.user_id)
        .outerjoin(StudyPlanBD, StudyPlanBD.id == StudyReminderBD.plan_id)
        .where(StudyReminderBD.status == "active", UserBD.is_active.is_(True),
               StudyReminderBD.next_notify_at <= now,
               or_(StudyReminderBD.lease_until.is_(None), StudyReminderBD.lease_until <= now),
               or_(StudyReminderBD.plan_id.is_(None), StudyPlanBD.status == "active"))
        .order_by(StudyReminderBD.next_notify_at, StudyReminderBD.id)
        .limit(100).with_for_update(skip_locked=True, of=StudyReminderBD)
    )).all()
    result, seen_users = [], set()
    for item, tg_id in rows:
        if len(result) >= 5:
            break
        if item.user_id in seen_users:
            continue
        if item.next_notify_at < now - timedelta(hours=24):
            advance_delivery(item, now)
            item.delivery_status = "missed"
            continue
        if item.attempts >= 5:
            clear_lease(item)
            item.status, item.delivery_status = "paused", "failed"
            continue
        token = str(uuid4())
        item.lease_token, item.lease_until = token, now + timedelta(minutes=3)
        item.attempts += 1
        result.append({"id": item.id, "token": token, "telegramId": tg_id,
                       "title": item.title, "targetPath": item.target_path,
                       "timezone": item.timezone, "dueAt": item.due_at})
        seen_users.add(item.user_id)
    await db.commit()
    return {"items": result}


@internal_router.post("/{reminder_id}/receipt")
async def record_receipt(reminder_id: int, body: ReceiptIn, db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(StudyReminderBD).where(StudyReminderBD.id == reminder_id).with_for_update())
    if item is None or item.lease_token != body.token or item.status != "active":
        return {"accepted": False}
    now = datetime.now(timezone.utc)
    clear_lease(item)
    if body.outcome == "sent":
        item.last_sent_at, item.delivery_status = now, "sent"
        advance_delivery(item, now)
    elif body.outcome in ("blocked", "failed") or item.attempts >= 5:
        item.status = "paused"
        item.delivery_status = body.outcome if body.outcome in ("blocked", "failed") else "failed"
    else:
        item.delivery_status = "retrying"
        item.next_notify_at = now + timedelta(seconds=body.retry_after or min(3600, 60 * 2 ** item.attempts))
    await db.commit()
    return {"accepted": True}
