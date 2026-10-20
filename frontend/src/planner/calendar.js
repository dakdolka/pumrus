export const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function zonedParts(value, zone) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date(value));
  return Object.fromEntries(parts.filter((p) => p.type !== "literal").map((p) => [p.type, p.value]));
}

export function localDate(value = new Date(), zone = "Europe/Moscow") {
  const p = zonedParts(value, zone);
  return `${p.year}-${p.month}-${p.day}`;
}

export function toInstant(day, clock, zone) {
  const [year, month, date] = day.split("-").map(Number);
  const [hour, minute] = clock.split(":").map(Number);
  const wall = Date.UTC(year, month - 1, date, hour, minute);
  let guess = wall;
  for (let index = 0; index < 4; index += 1) {
    const p = zonedParts(guess, zone);
    const offset = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute) - wall;
    if (offset === 0) {
      // Match Python zoneinfo's fold=0: pick the first instance of a repeated hour.
      const before = guess - 86400000;
      const prior = zonedParts(before, zone);
      const previousOffset = Date.UTC(+prior.year, +prior.month - 1, +prior.day, +prior.hour, +prior.minute) - before;
      const alternative = wall - previousOffset;
      const earlier = zonedParts(alternative, zone);
      const matches = Date.UTC(+earlier.year, +earlier.month - 1, +earlier.day, +earlier.hour, +earlier.minute) === wall;
      return new Date(matches ? Math.min(alternative, guess) : guess).toISOString();
    }
    guess -= offset;
  }
  throw new Error("Это время отсутствует при переводе часов. Выберите другое время.");
}

export function nextWeeklyDate(start, days, clock, zone, now = new Date()) {
  const day = new Date(`${start}T12:00:00Z`);
  for (let index = 0; index < 9; index += 1) {
    const date = day.toISOString().slice(0, 10);
    if (days.includes((day.getUTCDay() + 6) % 7)) {
      const instant = toInstant(date, clock, zone);
      if (new Date(instant) > now) return instant;
    }
    day.setUTCDate(day.getUTCDate() + 1);
  }
  throw new Error("Выберите дни недели и будущую дату начала.");
}

export function formatMoment(value, zone) {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: zone, day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
  }).format(new Date(value));
}
