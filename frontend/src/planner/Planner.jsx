import { useCallback, useEffect, useId, useRef, useState } from "react";
import { WEEKDAYS, formatMoment, localDate, nextWeeklyDate, toInstant, zonedParts } from "./calendar";
import "./planner.css";

const browserZone = () => Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Moscow";
const requestKey = () => window.crypto.randomUUID();
const zones = Intl.supportedValuesOf?.("timeZone") || ["Europe/Moscow", "Europe/Kaliningrad", "Asia/Yekaterinburg", "Asia/Novosibirsk", "Asia/Vladivostok", "UTC"];

async function allowNotifications() {
  const tg = window.Telegram?.WebApp;
  if (!tg?.requestWriteAccess || (tg.isVersionAtLeast && !tg.isVersionAtLeast("6.9"))
      || tg.initDataUnsafe?.user?.allows_write_to_pm || sessionStorage.getItem("umrus:reminder-write-access")) return;
  const allowed = await new Promise((resolve) => tg.requestWriteAccess(resolve));
  if (!allowed) throw new Error("Для напоминаний разреши боту писать или запусти его командой /start, затем сохрани расписание.");
  sessionStorage.setItem("umrus:reminder-write-access", "1");
}

function WeekPicker({ value, onChange }) {
  return <fieldset className="planner-week"><legend>Учебные дни</legend>
    <div>{WEEKDAYS.map((label, day) => <button type="button" key={day}
      aria-pressed={value.includes(day)} onClick={() => onChange(value.includes(day)
        ? value.filter((d) => d !== day) : [...value, day].sort())}>{label}</button>)}</div>
  </fieldset>;
}

function ScheduleFields({ value, onChange, repeated = true }) {
  const set = (name, next) => onChange({ ...value, [name]: next });
  return <>
    <div className="planner-field-row">
      <label>{repeated ? "Начать с" : "Дата"}<input type="date" required value={value.date}
        min={localDate(new Date(), value.timezone || "UTC")} onChange={(e) => set("date", e.target.value)} /></label>
      <label>Время<input type="time" required value={value.local_time} onChange={(e) => set("local_time", e.target.value)} /></label>
    </div>
    <label>Часовой пояс<select required value={value.timezone} onChange={(e) => set("timezone", e.target.value)}>
      {[...new Set([value.timezone, "UTC", "Europe/Moscow", ...zones])].map((zone) => <option key={zone}>{zone}</option>)}
    </select></label>
    {repeated && <WeekPicker value={value.weekdays} onChange={(days) => set("weekdays", days)} />}
  </>;
}

function Dialog({ title, onClose, children }) {
  const ref = useRef(null);
  const headingId = useId();
  useEffect(() => { ref.current.showModal(); }, []);
  return <dialog className="planner-dialog" aria-labelledby={headingId} ref={ref} onCancel={(event) => { event.preventDefault(); onClose(); }}>
    <div className="planner-dialog-head"><h2 id={headingId}>{title}</h2><button type="button" onClick={onClose} aria-label="Закрыть">×</button></div>
    {children}
  </dialog>;
}

function ReminderForm({ api, tasks, initial, onSaved, onClose }) {
  const existing = initial?.id;
  const query = new URLSearchParams(window.location.search);
  const parsed = initial?.targetPath?.match(/^\/(theory|practice)\/tasks\/(\d+)(?:\/topics\/(\d+)|\?topic=(\d+))?$/);
  const zone = initial?.timezone || browserZone();
  const due = initial?.nextNotifyAt || initial?.dueAt || new Date(Date.now() + 3600000).toISOString();
  const parts = zonedParts(due, zone);
  const [value, setValue] = useState(() => ({
    title: initial?.title || query.get("title") || "",
    activity: parsed?.[1] || (initial?.targetPath === "/practice/mistakes" ? "mistakes" : initial ? "custom" : query.get("activity") || "theory"),
    task_number: parsed?.[2] || query.get("task") || String(tasks[0]?.number || ""),
    topic_id: parsed?.[3] || parsed?.[4] || query.get("topic") || "",
    date: localDate(due, zone), local_time: initial?.weekdays?.length ? initial.localTime : `${parts.hour}:${parts.minute}`,
    timezone: zone, weekdays: initial?.weekdays || [],
  }));
  const [repeat, setRepeat] = useState(Boolean(initial?.weekdays?.length));
  const [topics, setTopics] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [key] = useState(requestKey);
  const [topicError, setTopicError] = useState("");
  const set = (name, next) => setValue((v) => ({ ...v, [name]: next }));
  const hasTask = ["theory", "practice"].includes(value.activity);

  useEffect(() => {
    let cancelled = false;
    setTopics([]);
    setTopicError("");
    if (hasTask && value.task_number) {
      api(`/v2/catalog/tasks/${value.task_number}`).then((data) => {
        if (!cancelled) setTopics(data.topics);
      }).catch(() => { if (!cancelled) setTopicError("Не удалось загрузить темы. Можно выбрать задание целиком."); });
    }
    return () => { cancelled = true; };
  }, [value.task_number, hasTask]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (repeat && !value.weekdays.length) throw new Error("Выберите дни повторения.");
      const dueAt = repeat
        ? nextWeeklyDate(value.date, value.weekdays, value.local_time, value.timezone)
        : toInstant(value.date, value.local_time, value.timezone);
      const payload = {
        request_key: key, title: value.title, activity: value.activity,
        task_number: hasTask ? Number(value.task_number) : null,
        topic_id: hasTask && value.topic_id ? Number(value.topic_id) : null,
        timezone: value.timezone, local_time: value.local_time,
        weekdays: repeat ? value.weekdays : [], due_at: dueAt,
      };
      if (!existing) await allowNotifications();
      await api(`/v2/planner/reminders${existing ? `/${existing}` : ""}`, {
        method: existing ? "PUT" : "POST", body: JSON.stringify(payload),
      });
      await onSaved();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <Dialog title={existing ? "Изменить напоминание" : "Новое напоминание"} onClose={busy ? () => {} : onClose}>
    <form className="planner-form" onSubmit={submit}>
      <label>Что сделать<input required maxLength={160} value={value.title} placeholder="Например, повторить причастия"
        onChange={(e) => set("title", e.target.value)} /></label>
      <label>Открыть по напоминанию<select aria-label="Открыть по напоминанию" value={value.activity} onChange={(e) => set("activity", e.target.value)}>
        <option value="theory">Теорию</option><option value="practice">Практику</option>
        <option value="mistakes">Повторение ошибок</option><option value="custom">Мой план · своё напоминание</option>
      </select></label>
      {hasTask && <>
        <label>Задание<select aria-label="Задание" required value={value.task_number} onChange={(e) => setValue({ ...value, task_number: e.target.value, topic_id: "" })}>
          <option value="" disabled>Выберите задание</option>
          {tasks.map((task) => <option key={task.id} value={task.number}>{task.number}. {task.title}</option>)}
        </select></label>
        <label>Тема<select aria-label="Тема" value={value.topic_id} onChange={(e) => set("topic_id", e.target.value)}>
          <option value="">Задание целиком</option>{topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}
        </select></label>
        {topicError && <small role="status">{topicError}</small>}
      </>}
      {!initial?.planId && <label className="planner-checkbox"><input type="checkbox" checked={repeat} onChange={(e) => setRepeat(e.target.checked)} />Повторять по дням недели</label>}
      <ScheduleFields value={value} onChange={setValue} repeated={repeat} />
      <p className="planner-help">Напоминание придёт в личный чат с ботом. Время указано в выбранном часовом поясе.</p>
      {error && <p className="planner-error" role="alert">{error}</p>}
      <button className="primary-button" disabled={busy}>{busy ? "Сохраняем…" : "Сохранить напоминание"}</button>
    </form>
  </Dialog>;
}

function PlanForm({ api, tasks, initial, onSaved, onClose }) {
  const [key] = useState(requestKey);
  const [value, setValue] = useState(() => ({
    title: "Мой план подготовки", activity: "mixed", task_numbers: tasks.map((t) => t.number),
    timezone: initial?.schedule.timezone || browserZone(),
    date: localDate(new Date(), initial?.schedule.timezone || browserZone()),
    local_time: initial?.schedule.local_time || "19:00", weekdays: initial?.schedule.weekdays || [0, 2, 4], end_by: "",
  }));
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const update = (next) => { setValue(next); setPreview(null); setError(""); };
  const set = (name, next) => update({ ...value, [name]: next });
  const payload = () => ({
    request_key: key, title: value.title, activity: value.activity, task_numbers: value.task_numbers,
    timezone: value.timezone, local_time: value.local_time, weekdays: value.weekdays,
    start_date: value.date, end_by: value.end_by || null,
  });

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      if (!value.weekdays.length) throw new Error("Выберите учебные дни.");
      if (initial) {
        await api(`/v2/planner/plans/${initial.id}/reschedule`, { method: "POST", body: JSON.stringify(payload()) });
        await onSaved();
      } else if (!preview) {
        if (!value.task_numbers.length) throw new Error("Выберите хотя бы одно задание.");
        setPreview(await api("/v2/planner/plans/preview", { method: "POST", body: JSON.stringify(payload()) }));
      } else {
        await allowNotifications();
        await api("/v2/planner/plans", { method: "POST", body: JSON.stringify(payload()) });
        await onSaved();
      }
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <Dialog title={initial ? "Перенести оставшиеся занятия" : "Составить план курса"} onClose={busy ? () => {} : onClose}>
    <form className="planner-form" onSubmit={submit}>
      {!initial && <>
        <label>Название плана<input required maxLength={160} value={value.title} onChange={(e) => set("title", e.target.value)} /></label>
        <label>Что проходить<select value={value.activity} onChange={(e) => set("activity", e.target.value)}>
          <option value="mixed">Теория и практика по очереди</option><option value="theory">Только теория</option><option value="practice">Только практика</option>
        </select></label>
        <fieldset className="planner-task-picker"><legend>Задания курса</legend>
          <button type="button" className="planner-text-button" onClick={() => set("task_numbers", value.task_numbers.length === tasks.length ? [] : tasks.map((t) => t.number))}>
            {value.task_numbers.length === tasks.length ? "Снять выбор" : "Выбрать все"}</button>
          <div>{tasks.map((task) => <label key={task.id} className="planner-checkbox" title={task.title}>
            <input type="checkbox" checked={value.task_numbers.includes(task.number)} onChange={() => set("task_numbers", value.task_numbers.includes(task.number)
              ? value.task_numbers.filter((n) => n !== task.number) : [...value.task_numbers, task.number])} />{task.number}
          </label>)}</div>
        </fieldset>
      </>}
      <ScheduleFields value={value} onChange={update} />
      {!initial && <label>Закончить до · необязательно<input type="date" value={value.end_by} min={value.date} onChange={(e) => set("end_by", e.target.value)} /></label>}
      <p className="planner-help">Одно занятие в каждый выбранный день. {initial ? "Пройденные занятия сохранятся, остальные получат новые даты." : "В смешанном плане сначала изучаем теорию задания, затем закрепляем её на практике."}</p>
      {preview && <section className="planner-preview" aria-live="polite">
        <strong>{preview.items.length} занятий · до {formatMoment(preview.items.at(-1).dueAt, value.timezone)}</strong>
        <ol>{preview.items.slice(0, 4).map((item, index) => <li key={index}><span>{formatMoment(item.dueAt, value.timezone)}</span>{item.title}</li>)}</ol>
        {preview.items.length > 4 && <small>И ещё {preview.items.length - 4} занятий в том же ритме.</small>}
      </section>}
      {error && <p className="planner-error" role="alert">{error}</p>}
      <button className="primary-button" disabled={busy}>{busy ? "Рассчитываем…" : initial ? "Обновить расписание" : preview ? "Создать план и включить напоминания" : "Посмотреть расписание"}</button>
    </form>
  </Dialog>;
}

export default function Planner(props) {
  const { api, authenticate, navigate, Shell, Loading, ErrorState } = props;
  const [data, setData] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editor, setEditor] = useState(null);
  const [filter, setFilter] = useState("upcoming");
  const [planFilter, setPlanFilter] = useState("");
  const [limit, setLimit] = useState(20);
  const [busy, setBusy] = useState(false);
  const [deletion, setDeletion] = useState(null);
  const isTelegram = Boolean(window.Telegram?.WebApp?.initData);
  const highlighted = Number(new URLSearchParams(window.location.search).get("reminder"));
  const load = useCallback(async () => {
    const [overview, catalog] = await Promise.all([api("/v2/planner"), api("/v2/catalog/tasks")]);
    setData(overview); setTasks(catalog);
  }, [api]);

  useEffect(() => {
    if (!isTelegram) { setLoading(false); return; }
    let cancelled = false;
    authenticate().then(load).then(() => {
      if (!cancelled && new URLSearchParams(window.location.search).get("new") === "1") setEditor({ type: "reminder" });
    }).catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [isTelegram, load]);

  useEffect(() => {
    if (data && highlighted) document.getElementById(`reminder-${highlighted}`)?.scrollIntoView({ block: "center" });
  }, [data, highlighted]);

  // Refresh due labels when the app is left open or brought back from the background.
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const refresh = () => { setNow(Date.now()); if (isTelegram && document.visibilityState === "visible") load().catch(() => {}); };
    const timer = window.setInterval(() => setNow(Date.now()), 60000);
    document.addEventListener("visibilitychange", refresh);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", refresh); };
  }, [isTelegram, load]);

  async function mutate(path, body, message, method = "POST") {
    setBusy(true); setNotice("");
    try {
      await api(`/v2/planner${path}`, { method, ...(body ? { body: JSON.stringify(body) } : {}) });
      setDeletion(null); await load(); setNotice(message);
    } catch (err) { setNotice(err.message); }
    finally { setBusy(false); }
  }

  function closeEditor() {
    setEditor(null);
    if (new URLSearchParams(window.location.search).has("new")) navigate("/planner");
  }
  async function saved() { await load(); closeEditor(); setNotice("Расписание сохранено. Напоминания придут в Telegram."); }

  const plans = data?.plans || [];
  const reminders = data?.reminders || [];
  const overdue = reminders.filter((r) => r.status === "active" && !r.weekdays.length && new Date(r.dueAt).getTime() < now);
  const visible = reminders.filter((item) => {
    if (planFilter && String(item.planId || "single") !== planFilter) return false;
    if (highlighted === item.id) return true;
    if (filter === "completed") return item.status === "completed";
    if (item.status === "completed") return false;
    return filter !== "today" || localDate(item.dueAt, item.timezone) === localDate(now, item.timezone);
  }).sort((a, b) => new Date(a.dueAt) - new Date(b.dueAt));

  return <Shell navigate={navigate} breadcrumbs={[{ label: "Мой план" }]}>
    <div className="planner-page">
      <section className="planner-heading"><p className="eyebrow">Мой план</p><h1>Учиться в своём ритме</h1>
        <p>Небольшие шаги к большому результату. Выбери удобное время — мы напомним о занятии в Telegram.</p>
        {isTelegram && <div className="planner-main-actions">
          <button className="primary-button" disabled={loading || !data} onClick={() => setEditor({ type: "plan" })}>Составить план курса</button>
          <button className="secondary-button" disabled={loading || !data} onClick={() => setEditor({ type: "reminder" })}>＋ Напоминание</button>
        </div>}
      </section>
      {!isTelegram && <section className="planner-empty"><h2>Твой план — в Telegram</h2><p>Открой приложение через бота: так мы сохраним расписание для твоего аккаунта и сможем присылать напоминания. Команда бота: /plan.</p></section>}
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {notice && <p className="planner-notice" role="status">{notice}</p>}
      {data && <>
        {plans.length > 0 && <section className="planner-plans" aria-label="Планы курса">
          {plans.map((plan) => <article key={plan.id} className="planner-plan">
            <div className="planner-plan-title"><h2>{plan.title}</h2><span>{plan.completed === plan.total ? "Пройден" : plan.status === "paused" ? "На паузе" : "В процессе"}</span></div>
            <p>{plan.completed} из {plan.total} занятий</p>
            <progress value={plan.completed} max={plan.total || 1} aria-label={`Пройдено ${plan.completed} из ${plan.total}`} />
            <div className="planner-row-actions">
              {plan.completed < plan.total && <>
                <button disabled={busy} onClick={() => mutate(`/plans/${plan.id}/actions`, { action: plan.status === "paused" ? "resume" : "pause" }, plan.status === "paused" ? "План продолжен. Просроченные занятия можно перенести." : "Уведомления плана на паузе.")}>{plan.status === "paused" ? "Продолжить" : "Пауза"}</button>
                <button disabled={busy} onClick={() => setEditor({ type: "plan", initial: plan })}>Изменить расписание</button>
              </>}
              <button disabled={busy} onClick={() => setDeletion({ type: "plan", id: plan.id, title: plan.title })}>Удалить</button>
            </div>
          </article>)}
        </section>}
        {overdue.length > 0 && <p className="planner-overdue-note">Осталось {overdue.length} занятий с прошедшей датой. Можно пройти их сейчас или выбрать новое время.</p>}
        <div className="planner-list-toolbar">
          <div className="planner-tabs" role="group" aria-label="Показать занятия">
            {[["upcoming", "Впереди"], ["today", "Сегодня"], ["completed", "Пройдено"]].map(([key, label]) => <button key={key} aria-pressed={filter === key} onClick={() => { setFilter(key); setLimit(20); }}>{label}</button>)}
          </div>
          {plans.length > 0 && <select aria-label="Фильтр по плану" value={planFilter} onChange={(e) => { setPlanFilter(e.target.value); setLimit(20); }}>
            <option value="">Все занятия</option><option value="single">Отдельные напоминания</option>{plans.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
          </select>}
        </div>
        <section className="planner-agenda" aria-label="Расписание занятий">
          {visible.slice(0, limit).map((item) => {
            const late = !item.weekdays.length && new Date(item.dueAt).getTime() < now && item.status === "active";
            const parentPaused = plans.find((p) => p.id === item.planId)?.status === "paused";
            return <article id={`reminder-${item.id}`} key={item.id} className={`planner-item${highlighted === item.id ? " highlighted" : ""}${item.status === "completed" ? " completed" : ""}`}>
              <div className="planner-item-date"><time dateTime={item.dueAt}>{formatMoment(item.dueAt, item.timezone)}</time><small>{item.timezone}</small></div>
              <div className="planner-item-body">
                <h3>{item.title}</h3>
                {item.weekdays.length > 0 && <p className="planner-recurrence">Каждую неделю · {item.weekdays.map((d) => WEEKDAYS[d]).join(", ")} · {item.localTime}</p>}
                {item.status === "completed" ? <span className="planner-badge done">Пройдено</span>
                  : parentPaused || item.status === "paused" ? <span className="planner-badge">На паузе</span>
                    : late ? <span className="planner-badge late">Можно перенести</span> : null}
                {item.deliveryStatus === "blocked" && <p className="planner-error">Бот не может написать. Запусти его командой /start и нажми «Продолжить».</p>}
                {item.deliveryStatus === "failed" && <p className="planner-error">Не удалось доставить уведомление. Проверь время и нажми «Продолжить».</p>}
                {item.deliveryStatus === "missed" && item.status !== "completed" && <p className="planner-help">Уведомление устарело. Выбери новое время, чтобы получить напоминание.</p>}
                {item.nextNotifyAt && new Date(item.nextNotifyAt).getTime() !== new Date(item.dueAt).getTime() && <p className="planner-help">Напомним: {formatMoment(item.nextNotifyAt, item.timezone)}</p>}
                <div className="planner-row-actions">
                  <button className="planner-open" onClick={() => navigate(item.targetPath)}>Открыть материал →</button>
                  {item.status !== "completed" && <>
                    <button disabled={busy} onClick={() => mutate(`/reminders/${item.id}/actions`, { action: "complete" }, "Занятие отмечено как пройденное.")}>{item.weekdays.length ? "Завершить повторения" : "Пройдено ✓"}</button>
                    <button disabled={busy} onClick={() => mutate(`/reminders/${item.id}/actions`, { action: "snooze", minutes: 60 }, "Напомним через час. Для плана на паузе сначала нажми «Продолжить».")}>Через час</button>
                    <button disabled={busy} onClick={() => setEditor({ type: "reminder", initial: item })}>Изменить</button>
                    <button disabled={busy} onClick={() => mutate(`/reminders/${item.id}/actions`, { action: item.status === "paused" ? "resume" : "pause" }, "Настройки напоминания обновлены.")}>{item.status === "paused" ? "Продолжить" : "Пауза"}</button>
                  </>}
                  <button disabled={busy} onClick={() => setDeletion({ type: "reminder", id: item.id, title: item.title })}>Удалить</button>
                </div>
              </div>
            </article>;
          })}
          {!visible.length && <div className="planner-empty"><span aria-hidden="true">✧</span><h2>{filter === "completed" ? "Здесь будут твои результаты" : filter === "today" ? "На сегодня всё свободно" : "Начни с небольшого шага"}</h2>
            <p>{filter === "completed" ? "После занятия нажми «Пройдено» — прогресс останется здесь. Показываем последние 100 завершённых занятий." : filter === "today" ? "Загляни в «Впереди» или запланируй новое занятие." : "Составь план подготовки или добавь напоминание о теме, которую хочешь пройти."}</p>
          </div>}
          {visible.length > limit && <button className="secondary-button" onClick={() => setLimit(limit + 20)}>Показать ещё</button>}
        </section>
      </>}
    </div>
    {editor?.type === "reminder" && <ReminderForm api={api} tasks={tasks} initial={editor.initial} onSaved={saved} onClose={closeEditor} />}
    {editor?.type === "plan" && <PlanForm api={api} tasks={tasks} initial={editor.initial} onSaved={saved} onClose={closeEditor} />}
    {deletion && <Dialog title="Удалить из расписания?" onClose={() => !busy && setDeletion(null)}>
      <p>{deletion.title}</p>{deletion.type === "plan" && <p>Все занятия этого плана тоже будут удалены.</p>}
      <div className="planner-main-actions"><button className="secondary-button" disabled={busy} onClick={() => setDeletion(null)}>Оставить</button>
        <button className="primary-button" disabled={busy} onClick={() => mutate(`/${deletion.type === "plan" ? "plans" : "reminders"}/${deletion.id}`, null, "Удалено из расписания.", "DELETE")}>Удалить</button></div>
    </Dialog>}
  </Shell>;
}
