import { useCallback, useEffect, useMemo, useState } from "react";
import "./app.css";


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


function useRoute() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const update = () => {
      setPath(window.location.pathname);
      const key = `umrus:scroll:${window.location.pathname}${window.location.search}`;
      const saved = Number(sessionStorage.getItem(key) || 0);
      requestAnimationFrame(() => window.scrollTo({ top: saved, behavior: "auto" }));
    };
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  const navigate = useCallback((nextPath) => {
    const url = new URL(nextPath, window.location.origin);
    if (url.pathname === window.location.pathname && url.search === window.location.search) return;
    sessionStorage.setItem(
      `umrus:scroll:${window.location.pathname}${window.location.search}`,
      String(window.scrollY),
    );
    window.history.pushState({}, "", nextPath);
    setPath(url.pathname);
    const saved = Number(
      sessionStorage.getItem(`umrus:scroll:${url.pathname}${url.search}`) || 0,
    );
    requestAnimationFrame(() => window.scrollTo({
      top: saved,
      behavior: saved ? "auto" : "smooth",
    }));
  }, []);

  return { path, navigate };
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
    theory: "M6 4.8A3.8 3.8 0 0 1 9.8 1H12v16H9.8A3.8 3.8 0 0 0 6 20.8V4.8Zm12 0A3.8 3.8 0 0 0 14.2 1H12v16h2.2a3.8 3.8 0 0 1 3.8 3.8V4.8Z",
    practice: "m5 16.8 9.9-9.9 2.2 2.2-9.9 9.9-3 .8.8-3Zm10.9-10.9 1.2-1.2a1.6 1.6 0 0 1 2.2 0l.9.9a1.6 1.6 0 0 1 0 2.2L19 9.1l-3.1-3.2Z",
    arrow: "m9 5 7 7-7 7",
    back: "m15 5-7 7 7 7",
    check: "m5 12 4 4L19 6",
    home: "M3.5 11.2 12 4l8.5 7.2M5.5 9.7V20h13V9.7M9.5 20v-6h5v6",
    bookmark: "M7 3.5h10v17L12 17l-5 3.5v-17Z",
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[type]} fill={type === "theory" ? "currentColor" : "none"}
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
        strokeLinejoin="round" />
    </svg>
  );
}


function Shell({ children, breadcrumbs = [], contextAction, navigate }) {
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

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate("/")} aria-label="На главную">
          <span className="brand-mark">У</span>
          <span>UmRus</span>
        </button>
      </header>

      {(breadcrumbs.length > 0 || contextAction) && (
        <div className="navigation-strip">
          <button className="home-button" onClick={() => navigate("/")} aria-label="На главную">
            <AppIcon type="home" />
          </button>
          <nav className="breadcrumbs" aria-label="Навигация">
            {breadcrumbs.map((item, index) => (
              <span className="breadcrumb-wrap" key={`${item.label}-${index}`}>
                {index > 0 && <span className="breadcrumb-separator">/</span>}
                <button
                  className={index === breadcrumbs.length - 1 ? "breadcrumb active" : "breadcrumb"}
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
            <button className="context-switch" onClick={contextAction.onClick}>
              <AppIcon type={contextAction.icon} />
              <span className="visually-hidden">{contextAction.label}</span>
            </button>
          )}
        </div>
      )}
      <main>{children}</main>
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
      <section className="hero">
        <div className="hero-orbit orbit-one" />
        <div className="hero-orbit orbit-two" />
        <p className="eyebrow">Подготовка без хаоса</p>
        <h1>Русский язык становится <em>понятным</em></h1>
        <div className="mode-grid">
          <button className="mode-card theory-card" onClick={() => navigate("/theory")}>
            <span className="mode-icon"><AppIcon type="theory" /></span>
            <span className="mode-index">01</span>
            <strong>Теория</strong>
            <span>Разобраться в правилах</span>
            <i><AppIcon type="arrow" /></i>
          </button>
          <button className="mode-card practice-card" onClick={() => navigate("/practice")}>
            <span className="mode-icon"><AppIcon type="practice" /></span>
            <span className="mode-index">02</span>
            <strong>Практика</strong>
            <span>Проверить себя</span>
            <i><AppIcon type="arrow" /></i>
          </button>
        </div>
      </section>
    </Shell>
  );
}


function TaskCatalog({ mode, navigate }) {
  const state = useRemote(() => api("/v2/catalog/tasks"), []);
  const isTheory = mode === "theory";
  const title = isTheory ? "Теория" : "Практика";
  return (
    <Shell
      navigate={navigate}
      breadcrumbs={[{ label: title, icon: mode }]}
    >
      <section className="catalog-title">
        <h1>{title}</h1>
        <InfoButton
          title={title}
          text={isTheory
            ? "Выберите номер задания, чтобы открыть связанные темы и правила."
            : "Выберите задание, затем доступную подборку упражнений. Ошибки появятся здесь отдельным режимом."}
        />
      </section>
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data && (
        <section className="task-list">
          {groupTasks(state.data).map((group) => (
            <div className={group.label ? "task-group" : "task-group standalone"} key={group.key}>
              {group.label && <div className="group-rail"><span>{group.label}</span></div>}
              <div className="task-group-rows">
                {group.tasks.map((task) => (
                  <button
                    className="task-row"
                    key={task.id}
                    onClick={() => navigate(`/${mode}/tasks/${task.number}`)}
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


function InfoButton({ title, text }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="info-button" aria-label={`О разделе «${title}»`} onClick={() => setOpen(true)}>
        ?
      </button>
      {open && (
        <div className="info-backdrop" role="presentation" onMouseDown={() => setOpen(false)}>
          <section className="info-popup" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <button className="popup-close" onClick={() => setOpen(false)} aria-label="Закрыть">×</button>
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


function TaskTheory({ taskNumber, navigate }) {
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
        onClick: () => navigate(`/practice/tasks/${taskNumber}?origin=theory`),
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
          {state.data.theory && <TheoryDocument document={state.data.theory} />}
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


function TopicTheory({ taskNumber, topicId, navigate }) {
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
        onClick: () => navigate(
          `/practice/tasks/${taskNumber}?topic=${topicId}&origin=theory`,
        ),
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
            ? <TheoryDocument document={state.data.theory} />
            : <EmptyCard text="Материал этой темы пока готовится." />}
        </>
      )}
    </Shell>
  );
}


function TheoryDocument({ document }) {
  const roots = useMemo(() => {
    const children = new Map();
    const ids = new Set(document.blocks.map((block) => block.id));
    document.blocks.forEach((block) => {
      const key = block.parentId && ids.has(block.parentId) ? block.parentId : null;
      children.set(key, [...(children.get(key) || []), block]);
    });
    return { roots: children.get(null) || [], children };
  }, [document]);

  return (
    <article className="theory-document">
      {roots.roots.map((block) => (
        <TheoryBlock key={block.id} block={block} childMap={roots.children} depth={0} />
      ))}
    </article>
  );
}


function TheoryBlock({ block, childMap, depth }) {
  const [sectionOpen, setSectionOpen] = useState(true);
  const children = childMap.get(block.id) || [];
  const markdown = block.data?.markdown || "";
  if (block.type === "section") {
    return (
      <details
        className={`theory-section depth-${Math.min(depth, 3)}`}
        open={sectionOpen}
        onToggle={(event) => setSectionOpen(event.currentTarget.open)}
      >
        <summary>
          <span>{block.data?.title || "Подраздел"}</span>
          <i>+</i>
        </summary>
        <div className="theory-section-content">
          {children.map((child) => (
            <TheoryBlock key={child.id} block={child} childMap={childMap} depth={depth + 1} />
          ))}
        </div>
      </details>
    );
  }

  let content;
  if (block.type === "callout") {
    content = (
      <aside className={`callout callout-${block.data?.variant || "note"}`}>
        <span>{calloutLabel(block.data?.variant)}</span>
        <MarkdownText value={markdown} />
      </aside>
    );
  } else if (block.type === "example") {
    content = (
      <div className="example-block">
        <span>Пример</span>
        <MarkdownText value={markdown} />
      </div>
    );
  } else if (block.type === "image") {
    const source = block.data?.sourceType === "inline_svg"
      ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(block.data?.svg || "")}`
      : block.data?.url;
    content = source ? (
      <figure className="theory-image">
        <img src={source} alt={block.data?.alt || ""} />
        {block.data?.caption && <figcaption>{block.data.caption}</figcaption>}
      </figure>
    ) : null;
  } else if (block.type === "list") {
    const items = block.data?.items || [];
    const ListTag = block.data?.style === "ordered" ? "ol" : "ul";
    content = (
      <ListTag className="theory-list">
        {items.map((item, index) => <li key={index}>{String(item?.text || item)}</li>)}
      </ListTag>
    );
  } else if (block.type === "table") {
    const rows = block.data?.rows || [];
    content = (
      <div className="table-scroll">
        <table>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {(row?.cells || row || []).map((cell, cellIndex) => (
                  <td key={cellIndex}>{String(cell?.text || cell || "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  } else if (block.type === "video_embed" && block.data?.url) {
    content = (
      <a className="video-link" href={block.data.url} target="_blank" rel="noreferrer">
        Открыть видео
        <AppIcon type="arrow" />
      </a>
    );
  } else {
    const variant = block.settings?.variant;
    if (variant === "heading_1") content = <h2>{markdown}</h2>;
    else if (variant === "heading_2") content = <h3>{markdown}</h3>;
    else content = <MarkdownText value={markdown} />;
  }

  return (
    <div className={`theory-block theory-block-${block.type}`}>
      {content}
      {children.length > 0 && (
        <div className="theory-nested">
          {children.map((child) => (
            <TheoryBlock key={child.id} block={child} childMap={childMap} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}


function calloutLabel(variant) {
  return {
    warning: "Обратите внимание",
    rule: "Правило",
    important: "Важно",
    tip: "Подсказка",
    note: "Примечание",
  }[variant] || "Примечание";
}


function MarkdownText({ value }) {
  return (
    <div className="rich-text">
      {String(value || "").split(/\n{2,}/).filter(Boolean).map((paragraph, index) => (
        <p key={index}><InlineMarkdown value={paragraph} /></p>
      ))}
    </div>
  );
}


function InlineMarkdown({ value }) {
  const parts = String(value || "").split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}


function PracticeTask({ taskNumber, navigate }) {
  const search = new URLSearchParams(window.location.search);
  const topicId = search.get("topic");
  const theoryOrigin = search.get("origin") === "theory";
  const suffix = topicId ? `?topic_id=${topicId}` : "";
  const state = useRemote(
    () => api(`/v2/practice/tasks/${taskNumber}/sets${suffix}`),
    [taskNumber, topicId],
  );
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
        onClick: () => {},
      } : {
        label: "Теория",
        icon: "bookmark",
        onClick: () => navigate(
          topicId
            ? `/theory/tasks/${taskNumber}/topics/${topicId}`
            : `/theory/tasks/${taskNumber}`,
        ),
      }}
    >
      {state.loading && <Loading />}
      {state.error && <ErrorState message={state.error} />}
      {state.data && (
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
                onClick={async () => {
                  try {
                    const session = await api("/v2/practice/sessions", {
                      method: "POST",
                      body: JSON.stringify({
                        exercise_set_id: set.id,
                        user_id: window.__umrusUserId || null,
                        limit: 20,
                      }),
                    });
                    const contextQuery = theoryOrigin
                      ? `?origin=theory`
                      : "";
                    navigate(`/practice/sessions/${session.id}${contextQuery}`);
                  } catch (error) {
                    window.alert(error.message);
                  }
                }}
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


function PracticeSession({ sessionId, navigate }) {
  const theoryOrigin = new URLSearchParams(window.location.search).get("origin") === "theory";
  const state = useRemote(
    () => api(`/v2/practice/sessions/${sessionId}`),
    [sessionId],
  );
  const [session, setSession] = useState(null);
  const [index, setIndex] = useState(0);
  const [response, setResponse] = useState({});
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [theoryLink, setTheoryLink] = useState(null);

  useEffect(() => {
    if (!state.data) return;
    setSession(state.data);
    setIndex(Math.min(state.data.currentPosition, state.data.items.length - 1));
  }, [state.data]);

  useEffect(() => {
    if (!session) return;
    const currentItem = session.items[index];
    if (!currentItem) return;
    const key = `umrus:draft:${session.id}:${currentItem.sessionItemId}`;
    try {
      setResponse(JSON.parse(localStorage.getItem(key) || "{}"));
    } catch {
      setResponse({});
    }
  }, [session?.id, index]);

  useEffect(() => {
    if (!session) return;
    const currentItem = session.items[index];
    if (!currentItem || !Object.keys(response).length) return;
    const key = `umrus:draft:${session.id}:${currentItem.sessionItemId}`;
    localStorage.setItem(key, JSON.stringify(response));
  }, [session?.id, index, response]);

  const navigateFromSession = useCallback((nextPath) => {
    if (!theoryOrigin && session?.status === "active") {
      api(`/v2/practice/sessions/${session.id}/close`, { method: "POST" }).catch(() => {});
    }
    navigate(nextPath);
  }, [navigate, session?.id, session?.status, theoryOrigin]);

  if (state.loading) {
    return <Shell navigate={navigate}><Loading /></Shell>;
  }
  if (state.error) {
    return <Shell navigate={navigate}><ErrorState message={state.error} /></Shell>;
  }
  if (!session) return null;

  const item = session.items[index];
  const answered = Boolean(result);
  const progress = ((index + (answered ? 1 : 0)) / session.items.length) * 100;

  async function submit() {
    if (!hasResponse(item, response) || submitting) return;
    setSubmitting(true);
    try {
      const answer = await api(
        `/v2/practice/sessions/${session.id}/items/${item.sessionItemId}/attempts`,
        { method: "POST", body: JSON.stringify({ response }) },
      );
      localStorage.removeItem(`umrus:draft:${session.id}:${item.sessionItemId}`);
      setResult(answer);
      setSession((current) => ({ ...current, status: answer.sessionStatus }));
    } catch (error) {
      window.alert(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  function next() {
    if (index + 1 >= session.items.length) return;
    setIndex((current) => current + 1);
    setResponse({});
    setResult(null);
  }

  const finished = answered && index + 1 >= session.items.length;
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
        onClick: () => navigateFromSession(
          session.context.topicId
            ? `/theory/tasks/${session.context.taskNumber}/topics/${session.context.topicId}`
            : `/theory/tasks/${session.context.taskNumber}`,
        ),
      } : {
        label: "Открыть теорию",
        icon: "bookmark",
        onClick: () => setTheoryLink({
          label: session.context.topicTitle || `Теория задания ${session.context.taskNumber}`,
          taskNumber: session.context.taskNumber,
          topicId: session.context.topicId,
        }),
      }}
    >
      <section className="trainer">
        <div className="trainer-meta">
          <span>{index + 1} / {session.items.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-track"><i style={{ width: `${progress}%` }} /></div>

        <div className="question-card">
          <p className="eyebrow">Выберите ответ</p>
          <QuestionPrompt item={item} />
          <Interaction
            item={item}
            response={response}
            setResponse={setResponse}
            disabled={answered}
          />
        </div>

        {result && <ResultCard result={result} onTheory={setTheoryLink} />}

        {!answered ? (
          <button
            className="primary-button"
            disabled={!hasResponse(item, response) || submitting}
            onClick={submit}
          >
            {submitting ? "Проверяем…" : "Проверить"}
          </button>
        ) : finished ? (
          <button className="primary-button" onClick={() => navigate("/practice")}>
            Завершить тренировку
          </button>
        ) : (
          <button className="primary-button" onClick={next}>
            Следующее упражнение
          </button>
        )}
      </section>
      {theoryLink && (
        <TheoryOverlay link={theoryLink} onClose={() => setTheoryLink(null)} />
      )}
    </Shell>
  );
}


function QuestionPrompt({ item }) {
  const content = item.prompt?.word || item.prompt?.content || "";
  if (item.interactionType === "stress_selection") return null;
  return <div className="question-text">{content}</div>;
}


function Interaction({ item, response, setResponse, disabled }) {
  if (item.interactionType === "single_choice") {
    return (
      <div className="choice-list">
        {(item.interaction?.options || []).map((option) => (
          <button
            key={option.key}
            className={response.optionKey === option.key ? "choice active" : "choice"}
            disabled={disabled}
            onClick={() => setResponse({ optionKey: option.key })}
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
            className={response.selectedCharacterIndex === position ? "selected" : ""}
            onClick={() => setResponse({ selectedCharacterIndex: position })}
          >
            {character}
          </button>
        ) : <span key={position}>{character}</span>)}
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
    />
  );
}


function hasResponse(item, response) {
  if (item.interactionType === "single_choice") return Boolean(response.optionKey);
  if (item.interactionType === "stress_selection") {
    return Number.isInteger(response.selectedCharacterIndex);
  }
  return Boolean(response.text?.trim());
}


function ResultCard({ result, onTheory }) {
  const correct = result.status === "correct";
  return (
    <div className={`result-card ${correct ? "correct" : "incorrect"}`}>
      <div className="result-title">
        <span><AppIcon type={correct ? "check" : "back"} /></span>
        <strong>{correct ? "Верно" : "Нужно повторить"}</strong>
      </div>
      {!correct && result.correctAnswer && (
        <p>Правильный ответ: <b>{result.correctAnswer}</b></p>
      )}
      {result.feedback?.message && <p>{result.feedback.message}</p>}
      {(result.feedback?.theoryLinks || []).map((link) => (
        <button className="theory-link" key={link.route} onClick={() => onTheory(link)}>
          <AppIcon type="theory" />
          {link.label}
        </button>
      ))}
    </div>
  );
}


function TheoryOverlay({ link, onClose }) {
  const state = useRemote(
    () => link.topicId
      ? api(`/v2/theory/topics/${link.topicId}`)
      : api(`/v2/catalog/tasks/${link.taskNumber}`),
    [link.topicId, link.taskNumber],
  );
  const document = state.data?.theory;

  useEffect(() => {
    const handle = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", handle);
    return () => window.removeEventListener("keydown", handle);
  }, [onClose]);

  return (
    <div className="overlay-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="theory-overlay"
        role="dialog"
        aria-modal="true"
        aria-label={link.label}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="overlay-handle" />
        <header>
          <div>
            <p className="eyebrow">Теория к упражнению</p>
            <h2>{state.data?.title || link.label}</h2>
          </div>
          <button onClick={onClose} aria-label="Закрыть">×</button>
        </header>
        <div className="overlay-scroll">
          {state.loading && <Loading />}
          {state.error && <ErrorState message={state.error} />}
          {state.data && (
            document
              ? <TheoryDocument document={document} />
              : <EmptyCard text="Связанная теория пока готовится." />
          )}
        </div>
      </section>
    </div>
  );
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
  if (path === "/practice") return { screen: "catalog", mode: "practice" };
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

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    const applyTheme = () => {
      const root = document.documentElement;
      const params = tg?.themeParams || {};
      const theme = tg?.colorScheme === "light" ? "light" : "dark";
      root.dataset.theme = theme;
      const values = {
        "--paper": params.bg_color,
        "--surface": params.secondary_bg_color || params.section_bg_color,
        "--ink": params.text_color,
        "--muted": params.hint_color,
        "--blue": params.button_color || params.link_color,
        "--button-text": params.button_text_color,
        "--line": params.section_separator_color,
      };
      Object.entries(values).forEach(([name, value]) => {
        if (value) root.style.setProperty(name, value);
      });
    };

    applyTheme();
    tg?.ready?.();
    tg?.expand?.();
    tg?.disableVerticalSwipes?.();
    try {
      tg?.requestFullscreen?.();
    } catch {
      // Older Telegram clients keep the expanded, non-fullscreen mode.
    }
    tg?.onEvent?.("themeChanged", applyTheme);
    return () => tg?.offEvent?.("themeChanged", applyTheme);
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
      window.__umrusUserId = payload.user.id;
    }).catch(() => {});
  }, []);

  if (route.screen === "home") return <Home navigate={navigate} />;
  if (route.screen === "catalog") {
    return <TaskCatalog mode={route.mode} navigate={navigate} />;
  }
  if (route.screen === "taskTheory") {
    return <TaskTheory taskNumber={route.taskNumber} navigate={navigate} />;
  }
  if (route.screen === "topicTheory") {
    return <TopicTheory {...route} navigate={navigate} />;
  }
  if (route.screen === "practiceTask") {
    return <PracticeTask taskNumber={route.taskNumber} navigate={navigate} />;
  }
  if (route.screen === "session") {
    return <PracticeSession sessionId={route.sessionId} navigate={navigate} />;
  }
  return <NotFound navigate={navigate} />;
}
