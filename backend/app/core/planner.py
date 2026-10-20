"""Calendar calculations shared by planner API and the durable delivery queue."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc


def checked_zone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Выберите существующий часовой пояс, например Europe/Moscow") from error


def wall_time(day: date, clock: str, zone: str) -> datetime:
    """First occurrence on fall-back; shift a nonexistent spring time forward.

    A round trip through UTC normalizes DST gaps consistently on every host.
    """
    local = datetime.combine(day, time.fromisoformat(clock), checked_zone(zone))
    return local.astimezone(UTC).astimezone(checked_zone(zone)).astimezone(UTC)


def next_weekly(after: datetime, weekdays: list[int], clock: str, zone: str) -> datetime:
    if not weekdays or any(day not in range(7) for day in weekdays):
        raise ValueError("Выберите хотя бы один день недели")
    local_day = after.astimezone(checked_zone(zone)).date()
    for offset in range(9):
        day = local_day + timedelta(days=offset)
        if day.weekday() in weekdays:
            candidate = wall_time(day, clock, zone)
            if candidate > after:
                return candidate
    raise ValueError("Не удалось рассчитать расписание")


def plan_dates(start: date, count: int, weekdays: list[int], clock: str, zone: str,
               now: datetime) -> list[datetime]:
    if start < now.astimezone(checked_zone(zone)).date():
        raise ValueError("Дата начала уже прошла")
    if start > now.astimezone(checked_zone(zone)).date() + timedelta(days=366):
        raise ValueError("Выберите начало в пределах ближайшего года")
    dates = []
    day = start
    for _ in range(2200):
        if day.weekday() in weekdays:
            candidate = wall_time(day, clock, zone)
            if candidate > now:
                dates.append(candidate)
                if len(dates) == count:
                    return dates
        day += timedelta(days=1)
    raise ValueError("План слишком длинный; выберите больше учебных дней")


def clear_lease(reminder) -> None:
    reminder.lease_token = None
    reminder.lease_until = None


def advance_delivery(reminder, now: datetime) -> None:
    """Missed occurrences are skipped, never replayed as a burst."""
    clear_lease(reminder)
    reminder.attempts = 0
    if reminder.weekdays:
        reminder.due_at = next_weekly(now, reminder.weekdays,
                                      reminder.local_time, reminder.timezone)
        reminder.next_notify_at = reminder.due_at
    else:
        reminder.next_notify_at = None
