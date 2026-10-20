import test from "node:test";
import assert from "node:assert/strict";
import { localDate, nextWeeklyDate, toInstant } from "../src/planner/calendar.js";

test("chosen IANA zone is used independently of the device zone", () => {
  assert.equal(toInstant("2026-10-20", "19:00", "Europe/Moscow"), "2026-10-20T16:00:00.000Z");
  assert.equal(toInstant("2026-10-20", "19:00", "Asia/Vladivostok"), "2026-10-20T09:00:00.000Z");
  assert.equal(localDate("2026-10-20T21:30:00Z", "Europe/Moscow"), "2026-10-21");
});

test("weekly reminders select a future matching weekday", () => {
  const now = new Date("2026-10-20T15:00:00Z");
  assert.equal(nextWeeklyDate("2026-10-20", [1], "19:00", "Europe/Moscow", now), "2026-10-20T16:00:00.000Z");
  assert.equal(nextWeeklyDate("2026-10-20", [1], "17:00", "Europe/Moscow", now), "2026-10-27T14:00:00.000Z");
});

test("DST changes preserve the selected local hour", () => {
  assert.equal(toInstant("2026-03-28", "09:00", "Europe/Berlin"), "2026-03-28T08:00:00.000Z");
  assert.equal(toInstant("2026-03-29", "09:00", "Europe/Berlin"), "2026-03-29T07:00:00.000Z");
  assert.throws(() => toInstant("2026-03-29", "02:30", "Europe/Berlin"), /время отсутствует/);
  assert.equal(toInstant("2026-10-25", "02:30", "Europe/Berlin"), "2026-10-25T00:30:00.000Z");
});
