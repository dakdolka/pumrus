import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./app.css";
import { TheoryDocument } from "./theory/TheoryRenderer";
import BrandLogo from "./BrandLogo";


async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || "Не удалось выполнить запрос");
  }
  return response.json();
}


function reportAppError(error) {
  window.dispatchEvent(new CustomEvent("umrus:app-error", {
    detail: error?.message || "Не удалось выполнить действие",
  }));
}


function practiceClientId() {
  const key = "umrus:practice-client";
  let value = localStorage.getItem(key);
  if (!value) {
    value = window.crypto?.randomUUID?.()
      || `web-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(key, value);
  }
  return value;
}


async function openRelatedPractice(taskNumber, navigate, exerciseSetId = null, userId = null) {
  try {
    const data = await api(`/v2/practice/tasks/${taskNumber}/sets`);
    const taskSets = data.sets.filter((item) => !item.topicId);
    const requestedSet = exerciseSetId
      ? data.sets.find((item) => item.id === Number(exerciseSetId))
      : null;
    const set = requestedSet || (taskSets.length === 1
      ? taskSets[0]
      : data.sets.length === 1
        ? data.sets[0]
        : null);
    if (!set) throw new Error("Для задания не настроена единственная общая подборка");
    const session = await api("/v2/practice/sessions", {
      method: "POST",
      body: JSON.stringify({
        exercise_set_id: set.id,
        user_id: userId,
        client_session_id: practiceClientId(),
        mode: "standard",
        limit: set.sessionSize,
        page_size: set.pageSize,
      }),
    });
    navigate(`/practice/sessions/${session.id}?origin=theory`);
  } catch (error) {
    reportAppError(error);
  }
}


function routeScrollKey() {
  return `umrus:scroll:${window.location.pathname}${window.location.search}`;
}


function restoreRouteScroll(key) {
  const target = Math.max(0, Number(sessionStorage.getItem(key) || 0));
  let frame = 0;
  let attempts = 0;
  let stopped = false;
  const stop = () => {
    if (stopped) return;
    stopped = true;
    cancelAnimationFrame(frame);
    window.removeEventListener("wheel", stop);
    window.removeEventListener("touchstart", stop);
    window.removeEventListener("pointerdown", stop);
  };
  const apply = () => {
    if (stopped) return;
    window.scrollTo({ top: target, behavior: "auto" });
    attempts += 1;
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    if (Math.abs(window.scrollY - target) <= 2 || target <= maxScroll || attempts >= 300) {
      stop();
      return;
    }
    frame = requestAnimationFrame(apply);
  };
  window.addEventListener("wheel", stop, { passive: true });
  window.addEventListener("touchstart", stop, { passive: true });
  window.addEventListener("pointerdown", stop, { passive: true });
  frame = requestAnimationFrame(apply);
  return stop;
}


function useRoute() {
  const [location, setLocation] = useState(
    () => `${window.location.pathname}${window.location.search}`,
  );
  const currentScrollKey = useRef(routeScrollKey());
  const stopRestoring = useRef(() => {});

  useEffect(() => {
    const update = () => {
      sessionStorage.setItem(currentScrollKey.current, String(window.scrollY));
      currentScrollKey.current = routeScrollKey();
      setLocation(`${window.location.pathname}${window.location.search}`);
      stopRestoring.current();
      stopRestoring.current = restoreRouteScroll(currentScrollKey.current);
    };
    const save = () => sessionStorage.setItem(currentScrollKey.current, String(window.scrollY));
    window.history.scrollRestoration = "manual";
    window.addEventListener("popstate", update);
    window.addEventListener("pagehide", save);
    return () => {
      stopRestoring.current();
      window.removeEventListener("popstate", update);
      window.removeEventListener("pagehide", save);
    };
  }, []);

  const navigate = useCallback((nextPath) => {
    const url = new URL(nextPath, window.location.origin);
    if (url.pathname === window.location.pathname && url.search === window.location.search) return;
    sessionStorage.setItem(currentScrollKey.current, String(window.scrollY));
    window.history.pushState({}, "", nextPath);
    currentScrollKey.current = routeScrollKey();
    setLocation(`${url.pathname}${url.search}`);
    stopRestoring.current();
    stopRestoring.current = restoreRouteScroll(currentScrollKey.current);
  }, []);

  return { path: location.split("?")[0], navigate };
}


function useRemote(loader, dependencies) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  useEffect(() => {
    let active = true;
    setState({ loading: true, data: null, error: "" });
    loader()
      .then((data) => active && setState({ loading: false, data, error: "" }))
      .catch((error) => active && setState({
        loading: false,
        data: null,
        error: error.message,
      }));
    return () => { active = false; };
  }, dependencies);
  return state;
}


function AppIcon({ type }) {
  const paths = {
    theory: "M4.5 5.5c2.5-1.4 5-1.4 7.5.2v14c-2.5-1.6-5-1.6-7.5-.2v-14Zm15 0c-2.5-1.4-5-1.4-7.5.2v14c2.5-1.6 5-1.6 7.5-.2v-14ZM12 5.7v14",
    practice: "m5 16.8 9.9-9.9 2.2 2.2-9.9 9.9-3 .8.8-3Zm10.9-10.9 1.2-1.2a1.6 1.6 0 0 1 2.2 0l.9.9a1.6 1.6 0 0 1 0 2.2L19 9.1l-3.1-3.2Z",
    arrow: "m9 5 7 7-7 7",
    back: "m15 5-7 7 7 7",
    check: "m5 12 4 4L19 6",
    home: "M3.5 11.2 12 4l8.5 7.2M5.5 9.7V20h13V9.7M9.5 20v-6h5v6",
    bookmark: "M7 3.5h10v17L12 17l-5 3.5v-17Z",
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[type]} fill="none"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
        strokeLinejoin="round" />
    </svg>
  );
}


function Shell({ children, breadcrumbs = [], contextAction, navigate }) {
  const [notice, setNotice] = useState("");
  const backPath = breadcrumbs.length > 1
    ? breadcrumbs[breadcrumbs.length - 2].path
    : "/";

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    tg?.ready?.();
    tg?.expand?.();
    const handleBack = () => navigate(backPath || "/");
    if (breadcrumbs.length) {
      tg?.BackButton?.show?.();
      tg?.BackButton?.onClick?.(handleBack);
    } else {
      tg?.BackButton?.hide?.();
    }
    return () => tg?.BackButton?.offClick?.(handleBack);
  }, [backPath, breadcrumbs.length, navigate]);

  useEffect(() => {
    let timeout;
    const show = (event) => {
      window.clearTimeout(timeout);
      setNotice(String(event.detail || "Не удалось выполнить действие"));
      timeout = window.setTimeout(() => setNotice(""), 5000);
    };
    window.addEventListener("umrus:app-error", show);
    return () => {
      window.clearTimeout(timeout);
      window.removeEventListener("umrus:app-error", show);
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate("/")} aria-label="На главную">
          <BrandLogo />
        </button>
      </header>

      {(breadcrumbs.length > 0 || contextAction) && (
        <div className="navigation-strip">
          <div className="navigation-inner">
            <button className="home-button" onClick={() => navigate("/")} aria-label="На главную">
              <AppIcon type="home" />
            </button>
            <nav className="breadcrumbs" aria-label="Навигация">
              {breadcrumbs.map((item, index) => (
                <span className="breadcrumb-wrap" key={`${item.label}-${index}`}>
                  {index > 0 && <span className="breadcrumb-separator">/</span>}
                  <button
                    className={
                      !contextAction?.active && index === breadcrumbs.length - 1
                        ? "breadcrumb active"
                        : "breadcrumb"
                    }
                    onClick={() => item.path && navigate(item.path)}
                    disabled={!item.path}
                    aria-label={item.label}
                  >
                    {item.icon && <AppIcon type={item.icon} />}
                    {item.number && <span className="breadcrumb-number">{item.number}</span>}
                    {!item.icon && !item.number && item.label}
                  </button>
                </span>
              ))}
            </nav>
            {contextAction && (
              <button
                className={contextAction.active ? "context-switch active" : "context-switch"}
                onClick={contextAction.onClick}
              >
                <AppIcon type={contextAction.icon} />
                <span className="visually-hidden">{contextAction.label}</span>
              </button>
            )}
          </div>
        </div>
      )}
      <main>{children}</main>
      {notice && (
        <div className="app-notice" role="alert">
          <span>{notice}</span>
          <button onClick={() => setNotice("")} aria-label="Закрыть">×</button>
        </div>
      )}
    </div>
  );
}


function Loading() {
  return (
    <div className="state-card">
      <span className="loader" />
      <p>Загружаем материалы…</p>
    </div>
  );
}


function ErrorState({ message }) {
  return (
    <div className="state-card error-state">
      <span>Что-то пошло не так</span>
      <p>{message}</p>
      <button className="secondary-button" onClick={() => window.location.reload()}>
        Попробовать снова
      </button>
    </div>
  );
}


function Home({ navigate }) {
  return (
    <Shell navigate={navigate}>
      <div className="home-page">
      <section className="hero">
        <div className="hero-orbit orbit-one" />
        <div className="hero-orbit orbit-two" />
        <h1>
          <span>Русский язык —</span>
          <em>это легко</em>
        </h1>
        <div className="mode-grid">
          <button className="mode-card theory-card" onClick={() => navigate("/theory")}>
            <span className="mode-icon"><AppIcon type="theory" /></span>
            <span className="mode-copy">
              <strong>Теория</strong>
              <span>Разобраться в правилах</span>
            </span>
            <i><AppIcon type="arrow" /></i>
          </button>
          <button className="mode-card practice-card" onClick={() => navigate("/practice")}>
            <span className="mode-icon"><AppIcon type="practice" /></span>
            <span className="mode-copy">
              <strong>Практика</strong>
              <span>Проверить себя</span>
            </span>
            <i><AppIcon type="arrow" /></i>
          </button>
        </div>
      </section>
      <AppFooter />
      </div>
    </Shell>
  );
}


function AppFooter() {
  return (
    <footer className="app-footer">
      <span>UmRus · подготовка к ЕГЭ</span>
      <nav aria-label="Справка и контакты">
        <a href="https://t.me/dak_dolka" target="_blank" rel="noreferrer">
          Связаться
        </a>
        <InfoButton
          title="О проекте"
          text="UmRus помогает последовательно изучать правила русского языка и сразу закреплять их на практике."
          compact
        />
      </nav>
    </footer>
  );
}


function TaskCatalog({ mode, navigate, userId }) {
  const state = useRemote(() => api(`/v2/catalog/tasks?mode=${mode}`), [mode]);
  const isTheory = mode === "theory";
  const [startingTaskId, setStartingTaskId] = useState(null);
  const title = isTheory ? "Теория" : "Практика";

  async function openTask(task) {
    if (isTheory || !task.directExerciseSetId) {
      navigate(`/${mode}/tasks/${task.number}`);
      return;
    }
    setStartingTaskId(task.id);
    try {
      const session = await api("/v2/practice/sessions", {
        method: "POST",
        body: JSON.stringify({
          exercise_set_id: task.directExerciseSetId,
          user_id: userId,
          client_session_id: practiceClientId(),
          mode: "standard",
        }),
      });
      navigate(`/practice/sessions/${session.id}`);
    } catch (error) {
      setStartingTaskId(null);
      reportAppError(error);
    }
  }

  return (
    <Shell
      navigate={navigate}
      breadcrumbs={[{ label: title, icon: mode }]}
    >
      <section className="catalog-title">
        <h1>{title}</h1>
        <div className="catalog-actions">
          {isTheory && (
            <button className="deprecated-button" onClick={() => navigate("/theory/deprecated")}>Deprecated</button>
          )}
          <InfoButton
            title={title}
            text={isTheory
              ? "Выберите номер задания, чтобы открыть связанные темы и правила."
              : "Выберите задание, затем доступную подборку упражнений. Ошибки доступны отдельным режимом."}
          />
        </div>
      </section>
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data && (
        <section className="task-list">
          {!isTheory && (
            <div className="task-group standalone mistakes-task-group">
              <div className="task-group-rows">
                <button className="task-row mistakes-task-row" onClick={() => navigate("/practice/mistakes")}>
                  <span className="task-number">!</span>
                  <span className="task-content">
                    <strong>Отработать ошибки</strong>
                    <small>Повторить задания, в которых были ошибки</small>
                  </span>
                  <span className="row-arrow"><AppIcon type="arrow" /></span>
                </button>
              </div>
            </div>
          )}
          {groupTasks(state.data).map((group) => (
            <div className={group.label ? "task-group" : "task-group standalone"} key={group.key}>
              {group.label && <div className="group-rail"><span>{group.label}</span></div>}
              <div className="task-group-rows">
                {group.tasks.map((task) => (
                  <button
                    className={startingTaskId === task.id ? "task-row loading-row" : "task-row"}
                    key={task.id}
                    onClick={() => openTask(task)}
                    disabled={startingTaskId !== null}
                  >
                    <span className="task-number">{task.number}</span>
                    <span className="task-content">
                      <strong>{task.title || `Задание ${task.number}`}</strong>
                      {isTheory && task.topicCount > 0 && (
                        <small>{task.topicCount} {topicWord(task.topicCount)}</small>
                      )}
                    </span>
                    <span className="row-arrow"><AppIcon type="arrow" /></span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}
    </Shell>
  );
}


function DeprecatedTheory({ navigate, userId }) {
  const catalog = useRemote(() => api("/v2/theory/deprecated"), []);
  const [selectedId, setSelectedId] = useState(null);
  const document = useRemote(
    () => selectedId ? api(`/v2/theory/deprecated/${selectedId}`) : Promise.resolve(null),
    [selectedId],
  );
  const grouped = useMemo(() => {
    const groups = new Map();
    (catalog.data || []).forEach((item) => {
      const key = item.taskNumber ?? "other";
      groups.set(key, [...(groups.get(key) || []), item]);
    });
    return [...groups.entries()].sort(([a], [b]) => Number(a) - Number(b));
  }, [catalog.data]);
  return (
    <Shell navigate={navigate} breadcrumbs={[
      { label: "Теория", icon: "theory", path: "/theory" },
      { label: "Deprecated" },
    ]}>
      <section className="page-head compact-head">
        <p className="eyebrow">Архив без редактирования</p>
        <h1>Старая теория</h1>
        <p>Материалы из прежней версии UmRus. Они сохранены для сравнения и не заменяют актуальную теорию.</p>
      </section>
      {catalog.loading && <Loading />}
      {catalog.error && <ErrorState message={catalog.error} />}
      {!selectedId && catalog.data && (
        <section className="deprecated-list">
          {grouped.map(([number, items]) => (
            <div className="deprecated-group" key={number}>
              <strong>{number === "other" ? "Без задания" : `Задание ${number}`}</strong>
              <div>{items.map((item) => (
                <button key={item.versionId} onClick={() => setSelectedId(item.versionId)}>
                  <span>{item.topicTitle || item.title}</span><AppIcon type="arrow" />
                </button>
              ))}</div>
            </div>
          ))}
        </section>
      )}
      {selectedId && (
        <section className="deprecated-document">
          <button className="deprecated-back" onClick={() => setSelectedId(null)}><AppIcon type="back" /> К списку</button>
          {document.loading && <Loading />}
          {document.error && <ErrorState message={document.error} />}
          {document.data && <><h2>{document.data.title}</h2><TheoryDocument document={document.data} onPracticeNavigate={(targetTaskNumber, exerciseSetId) => openRelatedPractice(targetTaskNumber, navigate, exerciseSetId, userId)} /></>}
        </section>
      )}
    </Shell>
  );
}


function groupTasks(tasks) {
  const definitions = [
    { from: 1, to: 3, label: "Мини-текст" },
    { from: 4, to: 4, label: null },
    { from: 5, to: 7, label: "Лексика" },
    { from: 8, to: 8, label: null },
    { from: 9, to: 15, label: "Орфография" },
    { from: 16, to: 21, label: "Пунктуация" },
    { from: 22, to: 22, label: null },
    { from: 23, to: 26, label: "Текст" },
    { from: 27, to: 27, label: null },
  ];
  return definitions
    .map((definition) => ({
      ...definition,
      key: `${definition.from}-${definition.to}`,
      tasks: tasks.filter(
        (task) => task.number >= definition.from && task.number <= definition.to,
      ),
    }))
    .filter((group) => group.tasks.length);
}


function InfoButton({ title, text, compact = false }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef(null);
  const closeRef = useRef(null);
  const close = useCallback(() => {
    setOpen(false);
    requestAnimationFrame(() => triggerRef.current?.focus());
  }, []);
  useEffect(() => {
    if (!open) return undefined;
    closeRef.current?.focus();
    const handleKeyDown = (event) => event.key === "Escape" && close();
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [close, open]);
  return (
    <>
      <button
        ref={triggerRef}
        className={compact ? "info-button compact" : "info-button"}
        aria-label={`О разделе «${title}»`}
        onClick={() => setOpen(true)}
      >
        ?
      </button>
      {open && (
        <div className="info-backdrop" role="presentation" onMouseDown={close}>
          <section className="info-popup" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <button ref={closeRef} className="popup-close" onClick={close} aria-label="Закрыть">×</button>
            <p className="eyebrow">О разделе</p>
            <h2>{title}</h2>
            <p>{text}</p>
          </section>
        </div>
      )}
    </>
  );
}


function topicWord(count) {
  const tail = count % 10;
  const lastTwo = count % 100;
  if (tail === 1 && lastTwo !== 11) return "тема";
  if (tail >= 2 && tail <= 4 && !(lastTwo >= 12 && lastTwo <= 14)) return "темы";
  return "тем";
}


function TaskTheory({ taskNumber, navigate, userId }) {
  const state = useRemote(
    () => api(`/v2/catalog/tasks/${taskNumber}`),
    [taskNumber],
  );
  return (
    <Shell
      navigate={navigate}
      breadcrumbs={[
        { label: "Теория", icon: "theory", path: "/theory" },
        { label: `Задание ${taskNumber}`, number: taskNumber },
      ]}
      contextAction={{
        label: "Практика",
        icon: "bookmark",
        active: false,
        onClick: () => openRelatedPractice(taskNumber, navigate, null, userId),
      }}
    >
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data && (
        <>
          <section className="page-head task-head">
            <p className="eyebrow">Задание {taskNumber}</p>
            <h1>{state.data.title}</h1>
            {state.data.shortDescription && <p>{state.data.shortDescription}</p>}
          </section>
          {state.data.theory && <TheoryDocument document={state.data.theory} onPracticeNavigate={(targetTaskNumber, exerciseSetId) => openRelatedPractice(targetTaskNumber, navigate, exerciseSetId, userId)} />}
          <section className="section-block">
            <div className="section-heading">
              <p className="eyebrow">По частям</p>
              <h2>Темы задания</h2>
            </div>
            {state.data.topics.length ? (
              <div className="topic-grid">
                {state.data.topics.map((topic, index) => (
                  <button
                    className="topic-card"
                    key={topic.id}
                    onClick={() => navigate(`/theory/tasks/${taskNumber}/topics/${topic.id}`)}
                  >
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{topic.title}</strong>
                    <i><AppIcon type="arrow" /></i>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyCard text="Темы для этого задания пока готовятся." />
            )}
          </section>
        </>
      )}
    </Shell>
  );
}


function TopicTheory({ taskNumber, topicId, navigate, userId }) {
  const state = useRemote(
    () => api(`/v2/theory/topics/${topicId}`),
    [topicId],
  );
  return (
    <Shell
      navigate={navigate}
      breadcrumbs={[
        { label: "Теория", icon: "theory", path: "/theory" },
        { label: `Задание ${taskNumber}`, number: taskNumber, path: `/theory/tasks/${taskNumber}` },
        { label: state.data?.title || "Тема" },
      ]}
      contextAction={{
        label: "Практика",
        icon: "bookmark",
        active: false,
        onClick: () => openRelatedPractice(taskNumber, navigate, null, userId),
      }}
    >
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data && (
        <>
          <section className="page-head topic-head">
            <p className="eyebrow">Задание {taskNumber} · тема</p>
            <h1>{state.data.title}</h1>
          </section>
          {state.data.theory
            ? <TheoryDocument document={state.data.theory} onPracticeNavigate={(targetTaskNumber, exerciseSetId) => openRelatedPractice(targetTaskNumber, navigate, exerciseSetId, userId)} />
            : <EmptyCard text="Материал этой темы пока готовится." />}
        </>
      )}
    </Shell>
  );
}


function PracticeTask({ taskNumber, navigate, userId }) {
  const search = new URLSearchParams(window.location.search);
  const topicId = search.get("topic");
  const theoryOrigin = search.get("origin") === "theory";
  const mistakesMode = search.get("mistakes") === "1";
  const suffix = topicId ? `?topic_id=${topicId}` : "";
  const state = useRemote(
    () => api(`/v2/practice/tasks/${taskNumber}/sets${suffix}`),
    [taskNumber, topicId],
  );
  const [autoStartingSetId, setAutoStartingSetId] = useState(null);
  const startSet = useCallback(async (set) => {
    try {
      const session = await api("/v2/practice/sessions", {
        method: "POST",
        body: JSON.stringify({
          exercise_set_id: set.id,
          user_id: userId,
          client_session_id: practiceClientId(),
          mode: mistakesMode ? "mistakes" : "standard",
          limit: set.sessionSize,
          page_size: set.pageSize,
        }),
      });
      const contextQuery = theoryOrigin ? "?origin=theory" : "";
      navigate(`/practice/sessions/${session.id}${contextQuery}`);
    } catch (error) {
      setAutoStartingSetId(-1);
      reportAppError(error);
    }
  }, [mistakesMode, navigate, theoryOrigin]);

  useEffect(() => {
    const onlySet = state.data?.sets?.length === 1
      ? state.data.sets[0]
      : null;
    if (!onlySet || autoStartingSetId !== null) return;
    setAutoStartingSetId(onlySet.id);
    startSet(onlySet);
  }, [autoStartingSetId, startSet, state.data]);

  return (
    <Shell
      navigate={navigate}
      breadcrumbs={theoryOrigin ? [
        { label: "Теория", icon: "theory", path: "/theory" },
        { label: `Задание ${taskNumber}`, number: taskNumber, path: `/theory/tasks/${taskNumber}` },
        ...(topicId ? [{
          label: state.data?.sets?.[0]?.topicTitle || "Тема",
          path: `/theory/tasks/${taskNumber}/topics/${topicId}`,
        }] : []),
      ] : [
        { label: "Практика", icon: "practice", path: "/practice" },
        { label: `Задание ${taskNumber}`, number: taskNumber },
      ]}
      contextAction={theoryOrigin ? {
        label: "Практика",
        icon: "bookmark",
        active: true,
        onClick: () => {},
      } : {
        label: "Теория",
        icon: "bookmark",
        active: false,
        onClick: () => navigate(
          topicId
            ? `/theory/tasks/${taskNumber}/topics/${topicId}`
            : `/theory/tasks/${taskNumber}`,
        ),
      }}
    >
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {autoStartingSetId > 0 && <Loading />}
      {state.data && autoStartingSetId !== state.data.sets?.[0]?.id && (
        <>
          <section className="page-head task-head">
            <p className="eyebrow">Практика · задание {taskNumber}</p>
            <h1>{state.data.task.title}</h1>
            <p>Выберите подборку. В одну сессию войдёт до 20 случайных упражнений.</p>
          </section>
          <section className="set-list">
            {state.data.sets.length ? state.data.sets.map((set) => (
              <button
                className="set-card"
                key={set.id}
                onClick={() => startSet(set)}
              >
                <span className="set-label">{set.topicTitle ? "Тема" : "Задание"}</span>
                <strong>{set.title}</strong>
                <small>{set.exerciseCount} упражнений в банке</small>
                <i><AppIcon type="arrow" /></i>
              </button>
            )) : <EmptyCard text="Для этого раздела пока нет опубликованных тренажёров." />}
          </section>
        </>
      )}
    </Shell>
  );
}


function MistakesPractice({ navigate, userId }) {
  const state = useRemote(
    () => userId ? api(`/v2/practice/mistakes?user_id=${userId}`) : Promise.resolve({ total: 0, tasks: [] }),
    [userId],
  );
  return (
    <Shell
      navigate={navigate}
      breadcrumbs={[
        { label: "Практика", icon: "practice", path: "/practice" },
        { label: "Ошибки" },
      ]}
    >
      <section className="page-head task-head">
        <p className="eyebrow">Практика</p>
        <h1>Отработать ошибки</h1>
        <p>Здесь собраны упражнения, в которых последний ответ был неверным.</p>
      </section>
      {!userId && <EmptyCard text="История ошибок появится после входа через Telegram." />}
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data?.tasks?.length ? (
        <section className="set-list">
          {state.data.tasks.map((task) => (
            <button
              className="set-card"
              key={task.number}
              onClick={() => navigate(`/practice/tasks/${task.number}?mistakes=1`)}
            >
              <span className="task-number">{task.number}</span>
              <strong>{task.title}</strong>
              <small>{task.count} упражнений для повторения</small>
              <i><AppIcon type="arrow" /></i>
            </button>
          ))}
        </section>
      ) : userId && !state.loading ? <EmptyCard text="Активных ошибок пока нет." /> : null}
    </Shell>
  );
}


function PracticeSession({ sessionId, navigate }) {
  const theoryOrigin = new URLSearchParams(window.location.search).get("origin") === "theory";
  const state = useRemote(
    () => api(`/v2/practice/sessions/${sessionId}`),
    [sessionId],
  );
  const [session, setSession] = useState(null);
  const [page, setPage] = useState(0);
  const [responses, setResponses] = useState({});
  const [results, setResults] = useState({});
  const [submittingId, setSubmittingId] = useState(null);
  const [errorResult, setErrorResult] = useState(null);
  const [, setPendingAdvance] = useState(null);
  const [activeItemId, setActiveItemId] = useState(null);
  const [relatedTheoryOpen, setRelatedTheoryOpen] = useState(false);
  const [relatedTheoryTopicId, setRelatedTheoryTopicId] = useState(null);

  useEffect(() => {
    if (!state.data) return;
    setSession(state.data);
    const savedResults = Object.fromEntries(
      state.data.items
        .filter((item) => item.result)
        .map((item) => [item.sessionItemId, item.result]),
    );
    const savedResponses = Object.fromEntries(
      state.data.items
        .filter((item) => item.result?.response)
        .map((item) => [item.sessionItemId, item.result.response]),
    );
    let drafts = {};
    try {
      drafts = JSON.parse(localStorage.getItem(`umrus:drafts:${state.data.id}`) || "{}");
    } catch {
      drafts = {};
    }
    setResults(savedResults);
    setResponses({ ...drafts, ...savedResponses });
    const size = state.data.configuration?.pageSize || 5;
    setPage(Math.floor(Math.min(state.data.currentPosition, state.data.items.length - 1) / size));
  }, [state.data]);

  useEffect(() => {
    if (!session) return;
    localStorage.setItem(`umrus:drafts:${session.id}`, JSON.stringify(responses));
  }, [session?.id, responses]);

  useEffect(() => {
    if (!session) return;
    const size = session.configuration?.pageSize || 5;
    const first = session.items
      .slice(page * size, page * size + size)
      .find((item) => item.state === "pending");
    setActiveItemId(first?.sessionItemId || null);
  }, [session?.id, page]);

  const dismissError = useCallback(() => {
    setErrorResult(null);
    setPendingAdvance((pending) => {
      if (pending?.itemId) {
        setActiveItemId(pending.itemId);
      } else if (pending?.nextPage) {
        window.setTimeout(() => {
          setPage((current) => current + 1);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }, 180);
      }
      return null;
    });
  }, []);

  useEffect(() => {
    if (!errorResult) return undefined;
    const dismiss = (event) => {
      if (event.target.closest?.(".answer-sheet button")) return;
      dismissError();
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [dismissError, errorResult]);

  const pauseSession = useCallback(() => {
    if (session?.status !== "active") return;
    fetch(`/api/v2/practice/sessions/${session.id}/pause`, {
      method: "POST",
      keepalive: true,
    }).catch(() => {});
  }, [session?.id, session?.status]);

  useEffect(() => {
    const pauseOnExit = () => pauseSession();
    window.addEventListener("pagehide", pauseOnExit);
    return () => window.removeEventListener("pagehide", pauseOnExit);
  }, [pauseSession]);

  useEffect(() => {
    if (!session?.id) return undefined;
    const sessionId = session.id;
    return () => {
      fetch(`/api/v2/practice/sessions/${sessionId}/pause`, {
        method: "POST",
        keepalive: true,
      }).catch(() => {});
    };
  }, [session?.id]);

  const navigateFromSession = useCallback((nextPath) => {
    pauseSession();
    navigate(nextPath);
  }, [navigate, pauseSession]);

  if (state.loading) {
    return <Shell navigate={navigate}><Loading /></Shell>;
  }
  if (state.error) {
    return <Shell navigate={navigate}><ErrorState message={state.error} /></Shell>;
  }
  if (!session) return null;
  if (session.status === "expired") {
    return (
      <Shell navigate={navigate}>
        <div className="state-card">
          <strong>Сессия завершена</strong>
          <p>После выхода прошло больше 10 минут.</p>
          <button
            className="primary-button"
            onClick={() => navigate(`/practice/tasks/${session.context.taskNumber}`)}
          >
            Начать новую
          </button>
        </div>
      </Shell>
    );
  }

  const pageSize = session.configuration?.pageSize || 5;
  const promptDisplay = session.configuration?.promptDisplay || "normal";
  const pageStart = page * pageSize;
  const pageItems = session.items.slice(pageStart, pageStart + pageSize);
  const answeredCount = session.items.filter(
    (item) => item.state !== "pending" || results[item.sessionItemId],
  ).length;
  const progress = Math.min(100, (answeredCount / session.items.length) * 100);
  const pageComplete = pageItems.every(
    (item) => item.state !== "pending" || results[item.sessionItemId],
  );
  const finished = pageComplete && pageStart + pageSize >= session.items.length;

  async function submit(item, response) {
    if (!hasResponse(item, response) || submittingId || results[item.sessionItemId]) return;
    setSubmittingId(item.sessionItemId);
    try {
      const answer = await api(
        `/v2/practice/sessions/${session.id}/items/${item.sessionItemId}/attempts`,
        { method: "POST", body: JSON.stringify({ response }) },
      );
      setResults((current) => ({ ...current, [item.sessionItemId]: answer }));
      setSession((current) => ({ ...current, status: answer.sessionStatus }));
      const next = pageItems.find(
        (candidate) => candidate.sessionItemId !== item.sessionItemId
          && candidate.state === "pending"
          && !results[candidate.sessionItemId],
      );
      if (answer.status !== "correct") {
        setErrorResult(answer);
        setPendingAdvance(
          next
            ? { itemId: next.sessionItemId }
            : { nextPage: pageStart + pageSize < session.items.length },
        );
        setActiveItemId(item.sessionItemId);
        return;
      }
      if (next) {
        setActiveItemId(next.sessionItemId);
      } else if (pageStart + pageSize < session.items.length) {
        window.setTimeout(() => {
          setPage((current) => current + 1);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }, 450);
      }
    } catch (error) {
      reportAppError(error);
    } finally {
      setSubmittingId(null);
    }
  }

  async function resetSession() {
    if (!window.confirm("Сбросить текущую сессию и начать заново?")) return;
    try {
      await api(`/v2/practice/sessions/${session.id}/reset`, { method: "POST" });
      localStorage.removeItem(`umrus:drafts:${session.id}`);
      navigate(`/practice/tasks/${session.context.taskNumber}`);
    } catch (error) {
      reportAppError(error);
    }
  }

  return (
    <Shell
      navigate={navigateFromSession}
      breadcrumbs={theoryOrigin ? [
        { label: "Теория", icon: "theory", path: "/theory" },
        {
          label: `Задание ${session.context.taskNumber}`,
          number: session.context.taskNumber,
          path: `/theory/tasks/${session.context.taskNumber}`,
        },
        ...(session.context.topicId ? [{
          label: session.context.topicTitle,
          path: `/theory/tasks/${session.context.taskNumber}/topics/${session.context.topicId}`,
        }] : []),
      ] : [
        { label: "Практика", icon: "practice", path: "/practice" },
        { label: "Сессия", number: session.context.taskNumber },
      ]}
      contextAction={theoryOrigin ? {
        label: "Вернуться к теории",
        icon: "bookmark",
        active: true,
        onClick: () => navigateFromSession(`/theory/tasks/${session.context.taskNumber}`),
      } : {
        label: "Открыть теорию",
        icon: "bookmark",
        active: relatedTheoryOpen,
        onClick: () => {
          setRelatedTheoryOpen((open) => !open);
          setRelatedTheoryTopicId(null);
        },
      }}
    >
      {relatedTheoryOpen ? (
        <RelatedTheory
          taskNumber={session.context.taskNumber}
          topicId={relatedTheoryTopicId}
          onSelectTopic={setRelatedTheoryTopicId}
        />
      ) : <section className="trainer">
        <div className="trainer-meta">
          <span>{Math.min(pageStart + 1, session.items.length)}–{Math.min(pageStart + pageSize, session.items.length)} / {session.items.length}</span>
          <span>{Math.round(progress)}%</span>
          {session.status === "active" && (
            <button className="session-reset" onClick={resetSession}>Сбросить</button>
          )}
        </div>
        <div className="progress-track"><i style={{ width: `${progress}%` }} /></div>

        <div className="question-batch">
          {pageItems.map((item, itemIndex) => {
            const result = results[item.sessionItemId];
            const response = responses[item.sessionItemId] || {};
            const setResponse = (next) => setResponses((current) => ({
              ...current,
              [item.sessionItemId]: next,
            }));
            return (
              <article
                className={`batch-question ${result?.status || ""} ${activeItemId === item.sessionItemId ? "active" : ""}`}
                key={item.sessionItemId}
                data-session-item-id={item.sessionItemId}
                onClick={() => !result && !errorResult && setActiveItemId(item.sessionItemId)}
              >
                <span className="batch-number">{pageStart + itemIndex + 1}</span>
                <div className="batch-content">
                  <QuestionPrompt item={item} result={result} displayMode={promptDisplay} />
                  {item.interactionType === "vowel_fill" ? (
                    <VowelWord item={item} response={response} result={result} displayMode={promptDisplay} />
                  ) : item.interactionType !== "single_choice" ? (
                    <Interaction
                      item={item}
                      response={response}
                      result={result}
                      setResponse={setResponse}
                      disabled={Boolean(result) || Boolean(errorResult) || submittingId === item.sessionItemId}
                      onAnswer={(next) => {
                        setResponse(next);
                        submit(item, next);
                      }}
                      onComplete={(next) => submit(item, next)}
                    />
                  ) : null}
                  {result && (
                    ["single_choice", "multiple_choice"].includes(item.interactionType)
                    || (item.interactionType === "vowel_fill" && result.status === "incorrect")
                  ) && (
                    <AnswerReview
                      item={item}
                      result={result}
                      showSingleLetterSuccess={Boolean(session.configuration?.showSingleLetterSuccess)}
                    />
                  )}
                </div>
                {result?.status === "correct" && <span className="batch-status"><AppIcon type="check" /></span>}
                {result?.status === "partial" && <span className="batch-status partial">½</span>}
              </article>
            );
          })}
        </div>
        {(() => {
          const item = pageItems.find((candidate) => candidate.sessionItemId === activeItemId);
          if (!item || !["single_choice", "vowel_fill"].includes(item.interactionType)) return null;
          const response = responses[item.sessionItemId] || {};
          const setResponse = (next) => setResponses((current) => ({
            ...current,
            [item.sessionItemId]: next,
          }));
          return (
            <SharedKeyboard
              item={item}
              response={response}
              setResponse={setResponse}
              letterKeys={session.configuration?.letterKeys || session.configuration?.vowelKeys}
              disabled={Boolean(errorResult) || submittingId === item.sessionItemId}
              onAnswer={(next) => {
                setResponse(next);
                submit(item, next);
              }}
            />
          );
        })()}

        {finished ? (
          <button className="primary-button" onClick={() => navigate("/practice")}>
            Завершить тренировку
          </button>
        ) : null}
      </section>}
      {!relatedTheoryOpen && errorResult && (
        <div className={`answer-sheet ${errorResult.status}`} role="alert">
          <button className="answer-sheet-close" onClick={dismissError} aria-label="Закрыть">×</button>
          <strong>{errorResult.status === "partial" ? "Частично верно" : "Нужно повторить"}</strong>
          {errorResult.correctAnswer && <p>Правильный ответ: <b>{errorResult.correctAnswer}</b></p>}
          {(errorResult.feedback?.theoryLinks || []).map((link) => (
            <button
              key={link.route}
              onClick={() => {
                setErrorResult(null);
                setRelatedTheoryTopicId(null);
                setRelatedTheoryOpen(true);
              }}
            >
              <AppIcon type="theory" /> Открыть теорию
            </button>
          ))}
        </div>
      )}
    </Shell>
  );
}


function RelatedTheory({ taskNumber, topicId, onSelectTopic }) {
  const taskScrollPosition = useRef(0);
  const previousTopicId = useRef(topicId);
  const taskState = useRemote(
    () => api(`/v2/catalog/tasks/${taskNumber}`),
    [taskNumber],
  );
  const topicState = useRemote(
    () => topicId ? api(`/v2/theory/topics/${topicId}`) : Promise.resolve(null),
    [topicId],
  );
  useEffect(() => {
    const previous = previousTopicId.current;
    previousTopicId.current = topicId;
    if (!previous && topicId) {
      taskScrollPosition.current = window.scrollY;
      window.scrollTo({ top: 0, behavior: "auto" });
    } else if (previous && !topicId) {
      requestAnimationFrame(() => window.scrollTo({
        top: taskScrollPosition.current,
        behavior: "auto",
      }));
    }
  }, [topicId]);
  if (taskState.loading || (topicId && topicState.loading)) return <Loading />;
  if (taskState.error) return <ErrorState message={taskState.error} />;
  if (topicId && topicState.error) return <ErrorState message={topicState.error} />;
  if (topicId && topicState.data) {
    return (
      <div className="related-theory">
        <button className="related-theory-back" onClick={() => onSelectTopic(null)}>
          <AppIcon type="back" /> Все темы задания {taskNumber}
        </button>
        <section className="page-head topic-head">
          <p className="eyebrow">Задание {taskNumber} · тема</p>
          <h1>{topicState.data.title}</h1>
        </section>
        {topicState.data.theory
          ? <TheoryDocument document={topicState.data.theory} />
          : <EmptyCard text="Материал этой темы пока готовится." />}
      </div>
    );
  }
  if (!taskState.data) return null;
  return (
    <div className="related-theory">
      <section className="page-head task-head">
        <p className="eyebrow">Теория · задание {taskNumber}</p>
        <h1>{taskState.data.title}</h1>
        {taskState.data.shortDescription && <p>{taskState.data.shortDescription}</p>}
      </section>
      {taskState.data.theory && <TheoryDocument document={taskState.data.theory} />}
      <section className="section-block">
        <div className="section-heading"><p className="eyebrow">По частям</p><h2>Темы задания</h2></div>
        {taskState.data.topics.length ? (
          <div className="topic-grid">
            {taskState.data.topics.map((topic, index) => (
              <button className="topic-card" key={topic.id} onClick={() => onSelectTopic(topic.id)}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{topic.title}</strong>
                <i><AppIcon type="arrow" /></i>
              </button>
            ))}
          </div>
        ) : <EmptyCard text="Темы для этого задания пока готовятся." />}
      </section>
    </div>
  );
}


function revealCorrectChoice(content, correctAnswer) {
  const answer = String(correctAnswer || "").trim();
  if (!answer) return content;
  if (/^[а-яё]$/i.test(answer) && /_/.test(content)) {
    return content.replace(/_+/g, answer.toLocaleLowerCase("ru"));
  }
  if (/^НН?$/i.test(answer)) {
    return content.replace(/\(Н\/НН\)/gi, answer.toLocaleLowerCase("ru"));
  }
  if (/^(слитно|раздельно|дефис)$/i.test(answer)) {
    const separator = {
      слитно: "",
      раздельно: " ",
      дефис: "-",
    }[answer.toLocaleLowerCase("ru")];
    return content.replace(
      /\(([^()]+)\)/g,
      (match, fragment, offset, source) => {
        const hasLeftPart = /[а-яёa-z0-9]$/i.test(source.slice(0, offset));
        const hasRightPart = /^[а-яёa-z0-9]/i.test(
          source.slice(offset + match.length),
        );
        return `${hasLeftPart ? separator : ""}${fragment}${hasRightPart ? separator : ""}`;
      },
    ).replace(/--+/g, "-").replace(/ {2,}/g, " ");
  }
  return content;
}


function QuestionPrompt({ item, result, displayMode = "normal" }) {
  const rawContent = item.prompt?.word || item.prompt?.content || "";
  const content = result
    ? revealCorrectChoice(rawContent, result.correctAnswer)
    : rawContent;
  if (["stress_selection", "vowel_fill"].includes(item.interactionType)) return null;
  const isSingleToken = Boolean(content) && !/\s/.test(content.trim());
  const effectiveDisplay = item.prompt?.displayMode || displayMode;
  const contentParts = content.split(/(\s+)/);
  return (
    <div
      className={`question-text ${isSingleToken ? "single-token" : "sentence-prompt"} ${effectiveDisplay === "compact" ? "compact-text" : ""}`}
      title={content}
    >
      {contentParts.map((part, index) => (
        /^\s+$/.test(part)
          ? part
          : <span className="question-token" key={`${index}-${part}`}>{part}</span>
      ))}
    </div>
  );
}


function vowelFillState(item, response) {
  const mask = item.interaction?.mask || item.prompt?.content || "";
  const blanks = [...mask].reduce(
    (positions, character, index) => (
      character === "_" || character === "…" ? [...positions, index] : positions
    ),
    [],
  );
  const values = response.vowels || [];
  const word = [...mask].map((character, index) => {
    const slot = blanks.indexOf(index);
    return slot >= 0 ? (values[slot] || "•") : character;
  }).join("");
  return { mask, blanks, values, word };
}


function VowelWord({ item, response, result, displayMode = "normal" }) {
  const word = vowelFillState(item, response).word;
  const effectiveDisplay = item.prompt?.displayMode || displayMode;
  return (
    <div
      className={`vowel-word ${result ? result.status : ""} ${effectiveDisplay === "compact" ? "compact-text" : ""}`}
      title={word}
    >
      {word}
    </div>
  );
}


function answerText(item, response, fallback = "") {
  if (item.interactionType === "vowel_fill") return response?.text || fallback;
  if (item.interactionType === "single_choice") {
    const option = (item.interaction?.options || []).find(
      (candidate) => candidate.key === response?.optionKey,
    );
    return option?.label || fallback;
  }
  if (item.interactionType === "multiple_choice") {
    const selected = new Set(response?.optionKeys || []);
    const labels = (item.interaction?.options || [])
      .filter((candidate) => selected.has(candidate.key))
      .map((candidate) => candidate.label);
    return labels.length ? labels.join(", ") : fallback;
  }
  return fallback;
}


function AnswerReview({ item, result, showSingleLetterSuccess = false }) {
  const correct = answerText(item, result.correctResponse, result.correctAnswer);
  const selected = answerText(item, result.response);
  const prompt = item.prompt?.content || item.prompt?.word || "";
  const isSingleLetterGap = item.interactionType === "single_choice"
    && /_/.test(prompt)
    && /^[а-яё]$/i.test(String(result.correctAnswer || "").trim());
  if (result.status === "correct") {
    if (isSingleLetterGap && !showSingleLetterSuccess) return null;
    return <div className="answer-review correct"><span>Верно</span><b>{correct}</b></div>;
  }
  if (result.status === "partial") {
    return (
      <div className="answer-review partial">
        <span><small>Вы выбрали</small>{selected}</span>
        <span><small>Полный ответ</small><b>{correct}</b></span>
      </div>
    );
  }
  return (
    <div className="answer-review comparison">
      <span className="answer-review-wrong"><small>Ваш вариант</small><s>{selected}</s></span>
      <span className="answer-review-correct"><small>Правильно</small><b>{correct}</b></span>
    </div>
  );
}


function SharedKeyboard({ item, response, setResponse, letterKeys, disabled, onAnswer }) {
  if (item.interactionType === "single_choice") {
    return (
      <div className="shared-keyboard choice-list" aria-label="Варианты ответа">
        {(item.interaction?.options || []).map((option) => (
          <button key={option.key} disabled={disabled} onClick={() => onAnswer({ optionKey: option.key })}>
            {option.label}
          </button>
        ))}
      </div>
    );
  }
  const { mask, blanks, values } = vowelFillState(item, response);
  const choose = (letter) => {
    if (values.length >= blanks.length) return;
    const nextValues = [...values, letter];
    const text = [...mask].map((character, index) => {
      const slot = blanks.indexOf(index);
      return slot >= 0 ? (nextValues[slot] || "") : character;
    }).join("");
    const next = { text, vowels: nextValues };
    setResponse(next);
    if (nextValues.length === blanks.length) onAnswer(next);
  };
  return (
    <div className="shared-keyboard vowel-keyboard" aria-label="Клавиатура букв">
      {(letterKeys?.length ? letterKeys : ["а", "о", "е", "ё", "и", "ы", "у", "ю", "я", "э"]).map((letter) => (
        <button key={letter} disabled={disabled} onClick={() => choose(letter)}>{letter}</button>
      ))}
      <button
        disabled={disabled || !values.length}
        onClick={() => setResponse({ vowels: values.slice(0, -1) })}
      >⌫</button>
    </div>
  );
}


function Interaction({ item, response, result, setResponse, disabled, onAnswer, onComplete }) {
  if (item.interactionType === "single_choice") {
    return (
      <div className="choice-list">
        {(item.interaction?.options || []).map((option) => (
          <button
            key={option.key}
            className={response.optionKey === option.key ? "choice active" : "choice"}
            disabled={disabled}
            onClick={() => onAnswer({ optionKey: option.key })}
          >
            <i>{response.optionKey === option.key ? "●" : "○"}</i>
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    );
  }
  if (item.interactionType === "stress_selection") {
    const word = item.prompt?.word || "";
    const selectable = new Set(item.interaction?.selectablePositions || []);
    return (
      <div className="stress-word" aria-label="Выберите ударную гласную">
        {[...word].map((character, position) => selectable.has(position) ? (
          <button
            key={position}
            disabled={disabled}
            className={[
              result?.correctResponse?.selectedCharacterIndex === position ? "correct" : "",
              result?.status === "incorrect" && response.selectedCharacterIndex === position
                ? "wrong"
                : "",
              !result && response.selectedCharacterIndex === position ? "selected" : "",
            ].filter(Boolean).join(" ")}
            onClick={() => onAnswer({ selectedCharacterIndex: position })}
          >
            {character}
          </button>
        ) : <span key={position}>{character}</span>)}
      </div>
    );
  }
  if (item.interactionType === "multiple_choice") {
    const selected = new Set(response.optionKeys || []);
    const toggle = (key) => {
      const next = new Set(selected);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      setResponse({ optionKeys: [...next] });
    };
    return (
      <div className="multiple-choice-wrap">
        <div className="choice-list multiple-choice" aria-label="Выберите все подходящие варианты">
          {(item.interaction?.options || []).map((option) => (
            <button
              key={option.key}
              className={selected.has(option.key) ? "choice active" : "choice"}
              disabled={disabled}
              onClick={() => toggle(option.key)}
            >
              <i>{selected.has(option.key) ? "✓" : "○"}</i>
              <span>{option.label}</span>
            </button>
          ))}
        </div>
        <button
          className="multiple-submit"
          disabled={disabled || !selected.size}
          onClick={() => onComplete({ optionKeys: [...selected] })}
        >
          Проверить
        </button>
      </div>
    );
  }
  return (
    <input
      className="answer-input"
      value={response.text || ""}
      disabled={disabled}
      placeholder={item.interaction?.variant === "masked_letters"
        ? "Введите слово целиком"
        : "Введите ответ"}
      onChange={(event) => setResponse({ text: event.target.value })}
      onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
      onBlur={() => hasResponse(item, response) && onComplete(response)}
    />
  );
}


function hasResponse(item, response) {
  if (item.interactionType === "single_choice") return Boolean(response.optionKey);
  if (item.interactionType === "stress_selection") {
    return Number.isInteger(response.selectedCharacterIndex);
  }
  if (item.interactionType === "multiple_choice") {
    return Array.isArray(response.optionKeys) && response.optionKeys.length > 0;
  }
  if (item.interactionType === "vowel_fill") return Boolean(response.text);
  return Boolean(response.text?.trim());
}


function EmptyCard({ text }) {
  return <div className="empty-card">{text}</div>;
}


function NotFound({ navigate }) {
  return (
    <Shell navigate={navigate}>
      <div className="state-card">
        <h1>Страница не найдена</h1>
        <button className="primary-button" onClick={() => navigate("/")}>На главную</button>
      </div>
    </Shell>
  );
}


function resolveRoute(path) {
  let match;
  if (path === "/") return { screen: "home" };
  if (path === "/theory") return { screen: "catalog", mode: "theory" };
  if (path === "/theory/deprecated") return { screen: "deprecatedTheory" };
  if (path === "/practice") return { screen: "catalog", mode: "practice" };
  if (path === "/practice/mistakes") return { screen: "mistakesPractice" };
  match = path.match(/^\/theory\/tasks\/(\d+)\/topics\/(\d+)$/);
  if (match) return { screen: "topicTheory", taskNumber: +match[1], topicId: +match[2] };
  match = path.match(/^\/theory\/tasks\/(\d+)$/);
  if (match) return { screen: "taskTheory", taskNumber: +match[1] };
  match = path.match(/^\/practice\/tasks\/(\d+)$/);
  if (match) return { screen: "practiceTask", taskNumber: +match[1] };
  match = path.match(/^\/practice\/sessions\/(\d+)$/);
  if (match) return { screen: "session", sessionId: +match[1] };
  return { screen: "notFound" };
}


export default function App() {
  const { path, navigate } = useRoute();
  const route = resolveRoute(path);
  const [userId, setUserId] = useState(() => {
    const stored = Number(sessionStorage.getItem("umrus:user-id"));
    return Number.isInteger(stored) && stored > 0 ? stored : null;
  });

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    const browserTheme = window.matchMedia("(prefers-color-scheme: light)");
    const isTelegram = Boolean(tg?.initData);
    const applyTheme = () => {
      const root = document.documentElement;
      const theme = isTelegram
        ? (tg.colorScheme === "light" ? "light" : "dark")
        : (browserTheme.matches ? "light" : "dark");
      root.dataset.theme = theme;
      document.querySelector('meta[name="theme-color"]')?.setAttribute(
        "content",
        theme === "light" ? "#eceae6" : "#222129",
      );
    };

    applyTheme();
    if (isTelegram) {
      tg.ready?.();
      tg.expand?.();
      tg.disableVerticalSwipes?.();
      try {
        tg.requestFullscreen?.();
      } catch {
        // Older Telegram clients keep the expanded, non-fullscreen mode.
      }
      tg.onEvent?.("themeChanged", applyTheme);
    } else {
      browserTheme.addEventListener?.("change", applyTheme);
    }
    return () => {
      if (isTelegram) tg.offEvent?.("themeChanged", applyTheme);
      else browserTheme.removeEventListener?.("change", applyTheme);
    };
  }, []);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    const user = tg?.initDataUnsafe?.user;
    if (!user?.id) return;
    api("/users/get-or-create", {
      method: "POST",
      body: JSON.stringify({
        tg_id: String(user.id),
        name: user.first_name || "Ученик",
        second_name: user.last_name || "",
        username: user.username || null,
        avatar_url: user.photo_url || null,
      }),
    }).then((payload) => {
      const id = Number(payload.user.id);
      if (!Number.isInteger(id) || id <= 0) return;
      sessionStorage.setItem("umrus:user-id", String(id));
      setUserId(id);
    }).catch(() => {});
  }, []);

  if (route.screen === "home") return <Home navigate={navigate} />;
  if (route.screen === "catalog") {
    return <TaskCatalog mode={route.mode} navigate={navigate} userId={userId} />;
  }
  if (route.screen === "taskTheory") {
    return <TaskTheory taskNumber={route.taskNumber} navigate={navigate} userId={userId} />;
  }
  if (route.screen === "deprecatedTheory") {
    return <DeprecatedTheory navigate={navigate} userId={userId} />;
  }
  if (route.screen === "topicTheory") {
    return <TopicTheory {...route} navigate={navigate} userId={userId} />;
  }
  if (route.screen === "practiceTask") {
    return <PracticeTask taskNumber={route.taskNumber} navigate={navigate} userId={userId} />;
  }
  if (route.screen === "mistakesPractice") {
    return <MistakesPractice navigate={navigate} userId={userId} />;
  }
  if (route.screen === "session") {
    return <PracticeSession sessionId={route.sessionId} navigate={navigate} />;
  }
  return <NotFound navigate={navigate} />;
}
