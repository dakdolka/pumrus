import asyncio
import hashlib
import hmac
import json
import os
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v2.planner_router import internal_router, router
from app.core.config import settings
from app.core.db import Base, get_db
from app.core.planner import advance_delivery, next_weekly, plan_dates, wall_time
from app.infra.catalog.models import CourseBD, CourseVersionBD, ExamTaskBD, ExamTaskTopicBD, TopicBD
from app.infra.planner.models import StudyPlanBD, StudyReminderBD
from app.infra.user.general.models import UserBD

UTC = timezone.utc


class CalendarTests(unittest.TestCase):
    def test_moscow_wall_time_is_stable(self):
        self.assertEqual(wall_time(date(2026, 10, 20), "19:00", "Europe/Moscow"),
                         datetime(2026, 10, 20, 16, tzinfo=UTC))

    def test_spring_dst_keeps_local_hour(self):
        before = datetime(2026, 3, 28, 8, tzinfo=UTC)
        result = next_weekly(before, [6], "09:00", "Europe/Berlin")
        self.assertEqual(result, datetime(2026, 3, 29, 7, tzinfo=UTC))

    def test_nonexistent_time_moves_forward(self):
        self.assertEqual(wall_time(date(2026, 3, 29), "02:30", "Europe/Berlin"),
                         datetime(2026, 3, 29, 1, 30, tzinfo=UTC))

    def test_fall_dst_fires_once(self):
        first = wall_time(date(2026, 10, 25), "02:30", "Europe/Berlin")
        self.assertEqual(first, datetime(2026, 10, 25, 0, 30, tzinfo=UTC))
        self.assertEqual(next_weekly(first, [6], "02:30", "Europe/Berlin"),
                         datetime(2026, 11, 1, 1, 30, tzinfo=UTC))

    def test_same_day_future_and_past(self):
        now = datetime(2026, 10, 20, 15, tzinfo=UTC)
        self.assertEqual(next_weekly(now, [1], "19:00", "Europe/Moscow").day, 20)
        self.assertEqual(next_weekly(now, [1], "17:00", "Europe/Moscow").day, 27)

    def test_no_replay_after_outage(self):
        now = datetime(2026, 10, 20, 15, tzinfo=UTC)
        item = SimpleNamespace(weekdays=[0, 2, 4], local_time="19:00", timezone="Europe/Moscow",
                               due_at=now - timedelta(days=20), lease_token="old", lease_until=now, attempts=2)
        advance_delivery(item, now)
        self.assertEqual(item.due_at, datetime(2026, 10, 21, 16, tzinfo=UTC))
        self.assertIsNone(item.lease_token)
        self.assertEqual(item.attempts, 0)

    def test_plan_skips_past_time_today(self):
        dates = plan_dates(date(2026, 10, 20), 3, [0, 1, 2, 3, 4], "10:00", "Europe/Moscow",
                           datetime(2026, 10, 20, 12, tzinfo=UTC))
        self.assertEqual([value.day for value in dates], [21, 22, 23])

    def test_invalid_or_empty_schedule_rejected(self):
        with self.assertRaises(ValueError):
            next_weekly(datetime.now(UTC), [], "19:00", "Europe/Moscow")
        with self.assertRaises(ValueError):
            wall_time(date(2026, 10, 20), "19:00", "Invalid/Zone")

    def test_snoozed_weekly_notification_keeps_next_regular_occurrence(self):
        now = datetime(2026, 10, 20, 17, tzinfo=UTC)
        item = SimpleNamespace(weekdays=[0, 2, 4], local_time="19:00", timezone="Europe/Moscow",
                               due_at=datetime(2026, 10, 21, 16, tzinfo=UTC),
                               lease_token="old", lease_until=now, attempts=1)
        advance_delivery(item, now)
        self.assertEqual(item.due_at, datetime(2026, 10, 21, 16, tzinfo=UTC))


@unittest.skipUnless(os.getenv("PLANNER_TEST_DATABASE_URL"), "Set PLANNER_TEST_DATABASE_URL for PostgreSQL integration tests")
class PlannerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.schema = "planner_test_" + uuid4().hex
        self.engine = create_async_engine(os.environ["PLANNER_TEST_DATABASE_URL"])
        async with self.engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        isolated_engine = self.engine.execution_options(schema_translate_map={None: self.schema})
        tables = [UserBD.__table__, CourseBD.__table__, CourseVersionBD.__table__, ExamTaskBD.__table__,
                  TopicBD.__table__, ExamTaskTopicBD.__table__, StudyPlanBD.__table__, StudyReminderBD.__table__]
        async with isolated_engine.begin() as connection:
            await connection.run_sync(lambda conn: Base.metadata.create_all(conn, tables=tables))
        self.sessions = async_sessionmaker(isolated_engine, expire_on_commit=False)
        self.original_token = settings.telegram_bot_token
        self.original_internal = settings.backend_internal_token
        settings.telegram_bot_token = "123456:test-planner-token"
        settings.backend_internal_token = "test-planner-internal"
        app = FastAPI()
        app.include_router(router)
        app.include_router(internal_router)

        async def test_db():
            async with self.sessions() as session:
                yield session

        app.dependency_overrides[get_db] = test_db
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        async with self.sessions() as db:
            self.user = UserBD(tg_id="101", name="Student", is_active=True)
            other = UserBD(tg_id="202", name="Other", is_active=True)
            db.add_all([self.user, other])
            course = CourseBD(code="rus", title="Русский", status="published")
            db.add(course)
            await db.flush()
            version = CourseVersionBD(course_id=course.id, code="2026", title="ЕГЭ", is_active=True, status="published")
            db.add(version)
            await db.flush()
            for number in [4, 9, 10]:
                db.add(ExamTaskBD(course_version_id=version.id, code=str(number), number=number,
                                  title=f"Задание {number}", sort_order=number, status="published"))
            await db.commit()

    async def asyncTearDown(self):
        settings.telegram_bot_token = self.original_token
        settings.backend_internal_token = self.original_internal
        await self.client.aclose()
        async with self.engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        await self.engine.dispose()

    def auth(self, user="101"):
        values = {"auth_date": str(int(time.time())), "user": json.dumps({"id": int(user), "first_name": "Student"})}
        secret = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
        check = "\n".join(f"{key}={values[key]}" for key in sorted(values))
        values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        return {"X-Telegram-Init-Data": urlencode(values)}

    async def request(self, method, path="", body=None, user="101"):
        return await self.client.request(method, "/v2/planner" + path, json=body, headers=self.auth(user))

    async def internal(self, path, body=None):
        response = await self.client.post("/v2/internal/reminders" + path, json=body or {},
                                          headers={"X-Internal-Key": settings.backend_internal_token})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def reminder_body(self, **changes):
        return {"request_key": str(uuid4()), "title": "Повторить тему", "activity": "custom", "timezone": "Europe/Moscow",
                "local_time": "19:00", "due_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(), **changes}

    def plan_body(self, **changes):
        return {"request_key": str(uuid4()), "title": "Подготовка", "task_numbers": [10, 4, 9], "activity": "mixed",
                "timezone": "Europe/Moscow", "local_time": "19:00", "weekdays": [0, 2, 4],
                "start_date": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(), **changes}

    async def create(self, body=None):
        response = await self.request("POST", "/reminders", body or self.reminder_body())
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    async def make_due(self, reminder_id, **changes):
        async with self.sessions() as db:
            item = await db.get(StudyReminderBD, reminder_id)
            item.next_notify_at = item.due_at = datetime.now(UTC) - timedelta(minutes=1)
            for key, value in changes.items():
                setattr(item, key, value)
            await db.commit()

    async def test_auth_and_user_isolation(self):
        response = await self.client.get("/v2/planner", headers={"X-User-Id": str(self.user.id)})
        self.assertEqual(response.status_code, 401)
        self.assertEqual((await self.client.get("/v2/planner", headers={"X-Telegram-Init-Data": "hash=invalid"})).status_code, 401)
        item = await self.create()
        other = await self.request("GET", user="202")
        self.assertEqual(other.json()["reminders"], [])
        for method, path, body in [("DELETE", f"/reminders/{item['id']}", None),
                                   ("POST", f"/reminders/{item['id']}/actions", {"action": "complete"})]:
            self.assertEqual((await self.request(method, path, body, user="202")).status_code, 404)
        self.assertEqual((await self.client.post("/v2/internal/reminders/claim")).status_code, 401)

    async def test_create_idempotent_and_validation(self):
        body = self.reminder_body()
        first, second = await self.create(body), await self.create(body)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len((await self.request("GET")).json()["reminders"]), 1)
        invalid = [self.reminder_body(title="  "), self.reminder_body(timezone="Fake/Zone"),
                   self.reminder_body(due_at="2026-01-01T00:00:00"),
                   self.reminder_body(due_at=(datetime.now(UTC) - timedelta(days=1)).isoformat()),
                   self.reminder_body(activity="theory", task_number=99),
                   self.reminder_body(activity="theory", task_number=4, topic_id=999),
                   self.reminder_body(weekdays=[7]), self.reminder_body(local_time="25:00")]
        for value in invalid:
            self.assertEqual((await self.request("POST", "/reminders", value)).status_code, 422)

    async def test_plan_preview_create_progress_and_reschedule(self):
        body = self.plan_body()
        preview = await self.request("POST", "/plans/preview", body)
        self.assertEqual(preview.status_code, 200, preview.text)
        units = preview.json()["items"]
        self.assertEqual(len(units), 6)
        self.assertEqual(units[0]["targetPath"], "/theory/tasks/4")
        self.assertEqual(units[1]["targetPath"], "/practice/tasks/4")
        self.assertEqual((await self.request("GET")).json()["reminders"], [])
        created = await self.request("POST", "/plans", body)
        self.assertEqual(created.status_code, 201, created.text)
        plan_id = created.json()["id"]
        self.assertEqual((await self.request("POST", "/plans", body)).json()["id"], plan_id)
        overview = (await self.request("GET")).json()
        self.assertEqual(len(overview["reminders"]), 6)
        done = overview["reminders"][0]
        await self.request("POST", f"/reminders/{done['id']}/actions", {"action": "complete"})
        reschedule = {"start_date": (datetime.now(UTC) + timedelta(days=20)).date().isoformat(),
                      "local_time": "09:15", "timezone": "Asia/Vladivostok", "weekdays": [1, 3]}
        response = await self.request("POST", f"/plans/{plan_id}/reschedule", reschedule)
        self.assertEqual(response.status_code, 200, response.text)
        overview = (await self.request("GET")).json()
        self.assertEqual(overview["plans"][0]["completed"], 1)
        remaining = [i for i in overview["reminders"] if i["status"] != "completed"]
        self.assertTrue(all(i["timezone"] == "Asia/Vladivostok" for i in remaining))
        completed = next(i for i in overview["reminders"] if i["id"] == done["id"])
        self.assertEqual(completed["dueAt"], done["dueAt"])
        self.assertEqual((await self.request("DELETE", f"/plans/{plan_id}", user="202")).status_code, 404)
        await self.request("DELETE", f"/plans/{plan_id}")
        self.assertEqual((await self.request("GET")).json()["reminders"], [])

    async def test_plan_rejects_impossible_deadline_and_empty_week(self):
        body = self.plan_body(end_by=datetime.now(UTC).date().isoformat())
        self.assertEqual((await self.request("POST", "/plans", body)).status_code, 422)
        self.assertEqual((await self.request("POST", "/plans", self.plan_body(weekdays=[]))).status_code, 422)
        self.assertEqual((await self.request("GET")).json()["plans"], [])

    async def test_claim_receipt_and_duplicate_ack(self):
        item = await self.create()
        await self.make_due(item["id"])
        batch = await self.internal("/claim")
        self.assertEqual(len(batch["items"]), 1)
        claim = batch["items"][0]
        self.assertEqual((await self.internal("/claim"))["items"], [])
        receipt = {"token": claim["token"], "outcome": "sent"}
        self.assertTrue((await self.internal(f"/{item['id']}/receipt", receipt))["accepted"])
        self.assertFalse((await self.internal(f"/{item['id']}/receipt", receipt))["accepted"])
        result = (await self.request("GET")).json()["reminders"][0]
        self.assertEqual(result["deliveryStatus"], "sent")
        self.assertIsNone(result["nextNotifyAt"])
        self.assertEqual(result["status"], "active")  # Delivery does not imply learning completion.

    async def test_expired_lease_and_stale_receipt(self):
        item = await self.create()
        await self.make_due(item["id"])
        old = (await self.internal("/claim"))["items"][0]
        await self.make_due(item["id"], lease_until=datetime.now(UTC) - timedelta(seconds=1))
        new = (await self.internal("/claim"))["items"][0]
        self.assertNotEqual(old["token"], new["token"])
        self.assertFalse((await self.internal(f"/{item['id']}/receipt", {"token": old["token"], "outcome": "sent"}))["accepted"])
        await self.internal(f"/{item['id']}/receipt", {"token": new["token"], "outcome": "retry", "retry_after": 600})
        result = (await self.request("GET")).json()["reminders"][0]
        self.assertEqual(result["deliveryStatus"], "retrying")
        self.assertGreater(datetime.fromisoformat(result["nextNotifyAt"]), datetime.now(UTC) + timedelta(minutes=9))

    async def test_completed_and_paused_invalidate_claims(self):
        item = await self.create()
        await self.make_due(item["id"])
        claim = (await self.internal("/claim"))["items"][0]
        await self.request("POST", f"/reminders/{item['id']}/actions", {"action": "complete"})
        self.assertFalse((await self.internal(f"/{item['id']}/receipt", {"token": claim["token"], "outcome": "sent"}))["accepted"])
        self.assertEqual((await self.internal("/claim"))["items"], [])

    async def test_plan_pause_and_resume(self):
        created = await self.request("POST", "/plans", self.plan_body())
        plan_id = created.json()["id"]
        item = (await self.request("GET")).json()["reminders"][0]
        await self.make_due(item["id"])
        await self.request("POST", f"/plans/{plan_id}/actions", {"action": "pause"})
        self.assertEqual((await self.internal("/claim"))["items"], [])
        await self.request("POST", f"/plans/{plan_id}/actions", {"action": "resume"})
        self.assertEqual(len((await self.internal("/claim"))["items"]), 1)

    async def test_blocked_delivery_and_manual_resume(self):
        item = await self.create()
        await self.make_due(item["id"])
        claim = (await self.internal("/claim"))["items"][0]
        await self.internal(f"/{item['id']}/receipt", {"token": claim["token"], "outcome": "blocked"})
        result = (await self.request("GET")).json()["reminders"][0]
        self.assertEqual((result["status"], result["deliveryStatus"]), ("paused", "blocked"))
        response = await self.request("POST", f"/reminders/{item['id']}/actions", {"action": "resume"})
        self.assertEqual(response.json()["status"], "active")
        self.assertGreater(datetime.fromisoformat(response.json()["nextNotifyAt"]), datetime.now(UTC))

    async def test_weekly_send_advances_and_old_oneoff_is_not_replayed(self):
        due = next_weekly(datetime.now(UTC), [0, 2, 4], "19:00", "Europe/Moscow")
        item = await self.create(self.reminder_body(weekdays=[0, 2, 4], due_at=due.isoformat()))
        await self.make_due(item["id"])
        claim = (await self.internal("/claim"))["items"][0]
        await self.internal(f"/{item['id']}/receipt", {"token": claim["token"], "outcome": "sent"})
        result = (await self.request("GET")).json()["reminders"][0]
        self.assertGreater(datetime.fromisoformat(result["dueAt"]), datetime.now(UTC))
        old = await self.create()
        await self.make_due(old["id"], next_notify_at=datetime.now(UTC) - timedelta(days=2))
        self.assertEqual((await self.internal("/claim"))["items"], [])
        self.assertEqual(next(i for i in (await self.request("GET")).json()["reminders"] if i["id"] == old["id"])["deliveryStatus"], "missed")

    async def test_concurrent_workers_do_not_share_a_lease(self):
        item = await self.create()
        await self.make_due(item["id"])
        batches = await asyncio.gather(self.internal("/claim"), self.internal("/claim"))
        self.assertEqual(sum(len(batch["items"]) for batch in batches), 1)

    async def test_lost_receipts_have_a_bounded_retry_budget(self):
        item = await self.create()
        await self.make_due(item["id"], attempts=5)
        self.assertEqual((await self.internal("/claim"))["items"], [])
        result = (await self.request("GET")).json()["reminders"][0]
        self.assertEqual((result["status"], result["deliveryStatus"]), ("paused", "failed"))


if __name__ == "__main__":
    unittest.main()
