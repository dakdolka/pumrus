import { useRef, useState, useEffect } from "react";
import "./General.css";
import Chapter from "./components/Chapter/chapter.jsx";
import { Element, TaskElement, Popup } from "./components.jsx";
import { TaskSelect }       from "./components/trainers/TaskSelect.jsx";
import { UniversalTrainer } from "./components/trainers/UniversalTrainer.jsx";
import { getStorageKey }    from "./components/trainers/trainerUtils.js";


function saveInfo(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getInfo(key) {
  return JSON.parse(localStorage.getItem(key));
}


// ─── Option (для TheoryChoose) ────────────────────────────────────────────────

function Option({ children, onSelect, theme_id }) {
  const [isChosen, setMood] = useState(false);
  return (
    <div
      className="option"
      data-ischosen={isChosen.toString()}
      onClick={() => {
        setMood((prev) => {
          onSelect(theme_id, !prev);
          return !prev;
        });
      }}
    >
      <div className={isChosen ? "option__button option__button--active" : "option__button"} />
      <div className="option__nameBlock">
        <div className="option__name">{children}</div>
      </div>
    </div>
  );
}


// ─── TheoryChoose ─────────────────────────────────────────────────────────────

function TheoryChoose({
  preloadedRules, preloadedTasks, availableTypes,
  isPopup, setPopup, content, setContent,
}) {
  const task  = useRef();
  const theme = useRef();

  const [isTaskActive,  setTaskMood]    = useState(false);
  const [isThemeActive, setThemeMood]   = useState(false);
  const [chosenBlock,   setChosenBlock] = useState([]);
  const [viewRules,     setViewRules]   = useState([]);
  const [rules,         setRules]       = useState(preloadedRules || []);
  const [tasks,         setTasks]       = useState(preloadedTasks || []);

  useEffect(() => {
    if (!preloadedRules) {
      fetch(`/api/theory/all_theory`)
        .then((r) => r.json())
        .then(setRules)
        .catch(console.error);
    }
  }, [preloadedRules]);

  useEffect(() => {
    if (!preloadedTasks) {
      fetch(`/api/theory/get_tasks_theory`)
        .then((r) => r.json())
        .then(setTasks)
        .catch(console.error);
    }
  }, [preloadedTasks]);

  function handleSelect(id, isChoose) {
    setChosenBlock((prev) =>
      isChoose
        ? prev.includes(id) ? prev : [...prev, id]
        : prev.filter((item) => item !== id)
    );
  }

  useEffect(() => {
    if (chosenBlock.length === 0) {
      setViewRules(rules);
    } else {
      const filtered = [];
      rules.forEach((item) => {
        (item.types || []).forEach((type) => {
          if (chosenBlock.includes(type.id)) filtered.push(item);
        });
      });
      setViewRules(filtered);
    }
  }, [chosenBlock, rules]);

  function showContent(parent) {
    if (parent === "task") {
      setTaskMood((prev) => !prev);
      if (isThemeActive) setThemeMood(false);
    } else {
      setThemeMood((prev) => !prev);
      if (isTaskActive) setTaskMood(false);
    }
  }

  return (
    <>
      <div className="theoryChoose">
        <div
          ref={task}
          className={isTaskActive
            ? "theoryChoose__elem theoryChoose__task--active"
            : "theoryChoose__elem theoryChoose__task--hidden"}
          onClick={() => showContent("task")}
        >
          Задания
        </div>
        <div
          ref={theme}
          className={isThemeActive
            ? "theoryChoose__elem theoryChoose__theme--active"
            : "theoryChoose__elem theoryChoose__theme--hidden"}
          onClick={() => showContent("theme")}
        >
          Темы
        </div>
      </div>

      <div className={isThemeActive
        ? "theoryChoose__block theoryChoose__block--active"
        : "theoryChoose__block--hidden"}
      >
        {(availableTypes || []).map((type) => (
          <Option key={type.id} theme_id={type.id} onSelect={handleSelect}>
            {type.name}
          </Option>
        ))}
      </div>

      <div className={isThemeActive ? "elementBlock elementBlock--small" : "elementBlock elementBlock--big"}>
        {isTaskActive === false
          ? viewRules.map((item, index) => (
              <Element
                key={index}
                theory_id={item.id}
                setPopup={setPopup}
                setContent={setContent}
              >
                {item.name}
              </Element>
            ))
          : tasks.map((item, index) => (
              <TaskElement
                key={index}
                is_single={item.is_single}
                content={item.tasks}
                setPopup={setPopup}
                setContent={setContent}
              >
                {item.group_name}
              </TaskElement>
            ))
        }
      </div>
    </>
  );
}


// ─── App ──────────────────────────────────────────────────────────────────────

function App() {
  const day_task       = useRef();
  const task           = useRef();
  const theory         = useRef();
  const analysis       = useRef();
  const title          = useRef();
  const trainerExitRef = useRef(null);

  const [userId,       setUserId]       = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [allTasks,     setAllTasks]     = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError,   setTasksError]   = useState('');

  const [isFadingOut,          setIsFadingOut]          = useState(false);
  const [showLoadingIndicator, setShowLoadingIndicator] = useState(false);
  const [isContentReady,       setIsContentReady]       = useState(false);
  const [theoryCache,          setTheoryCache]          = useState({});
  const [page,                 setPage]                 = useState("subject");

  const [isTheoryPopupOpen,  setIsTheoryPopupOpen]  = useState(false);
  const [theoryPopupContent, setTheoryPopupContent] = useState({ title: "Отсутствует", blocks: [] });


  // ── Загрузка заданий ──────────────────────────────────
  async function loadTasks() {
    setTasksLoading(true);
    setTasksError('');
    try {
      const all = await fetch('/api/tasks/general/').then(r => r.json());
      const active = all.filter(t => t.items?.length > 0);
      setAllTasks(active);
    } catch (e) {
      console.error('loadTasks error:', e);
      setTasksError('Не удалось загрузить задания');
    } finally {
      setTasksLoading(false);
    }
  }


  // ── Telegram WebApp init ───────────────────────────────
  useEffect(() => {
    const tg = window.Telegram?.WebApp || {};
    tg.ready?.();
    tg.expand?.();

    const tgUser = tg.initDataUnsafe?.user;
    if (tgUser?.id) setUserId(String(tgUser.id));

    const params = tg.themeParams || {};
    const isDark = tg.colorScheme === "dark";
    const root   = document.documentElement;
    const setVar = (name, value) => { if (value) root.style.setProperty(`--${name}`, value); };

    document.body.classList.toggle("theme--light", !isDark);
    document.body.classList.toggle("theme--dark",   isDark);

    setVar("text-color",  params.text_color);
    setVar("main-color",  params.bg_color);
    setVar("block-color", params.secondary_bg_color || params.section_bg_color);

    const accent = isDark ? "rgb(255, 200, 100)" : params.header_bg_color || "#3b6fd4";
    const mix    = isDark ? "10%" : "7%";
    setVar("active-color", accent);
    root.style.setProperty("--rule-color", `color-mix(in srgb, ${accent} ${mix}, transparent)`);
  }, []);


  // ── Touch-эффекты ─────────────────────────────────────
  useEffect(() => {
    const onStart = (e) => {
      const btn = e.target.closest("button");
      if (btn) btn.classList.add("is-pressed");
    };
    const onEnd = (e) => {
      const btn = e.target.closest("button");
      if (btn) setTimeout(() => btn.classList.remove("is-pressed"), 270);
    };
    document.addEventListener("touchstart", onStart, { passive: true });
    document.addEventListener("touchend",   onEnd,   { passive: true });
    return () => {
      document.removeEventListener("touchstart", onStart);
      document.removeEventListener("touchend",   onEnd);
    };
  }, []);


  // ── Переход с анимацией ────────────────────────────────
  async function performTransition(action, { withLoadingSpinner = true } = {}) {
    setIsFadingOut(true);
    await new Promise(r => setTimeout(r, 300));
    setIsContentReady(false);

    let loadingTimer;
    if (withLoadingSpinner) {
      loadingTimer = setTimeout(() => setShowLoadingIndicator(true), 300);
    }

    await action?.();
    await new Promise(r => setTimeout(r, 50));

    setIsContentReady(true);
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 50))));

    clearTimeout(loadingTimer);
    setShowLoadingIndicator(false);
    setIsFadingOut(false);
  }


  // ── Telegram BackButton ────────────────────────────────
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    const handleBack = async () => {
      setShowLoadingIndicator(false);

      if (isTheoryPopupOpen) { setIsTheoryPopupOpen(false); return; }

      // Внутри тренажёра — выход обрабатывает UniversalTrainer
      if (page === "trainers" && selectedTask) return;

      const backMap = {
        theory:     "subject",
        trainers:   "subject",
        analysis:   "subject",
        "day-task": "subject",
      };

      const targetPage = backMap[page];
      if (!targetPage) { tg.close?.(); return; }

      await performTransition(() => {
        setPage(targetPage);
        if (targetPage === "subject") setSelectedTask(null);
      }, { withLoadingSpinner: false });
    };

    if (["subject", "theory", "trainers", "analysis", "day-task"].includes(page)) {
      tg.BackButton.show();
      tg.onEvent("backButtonClicked", handleBack);
    } else {
      tg.BackButton.hide();
    }

    return () => tg.offEvent?.("backButtonClicked", handleBack);
  }, [page, isTheoryPopupOpen, selectedTask]);


  // ── Первый рендер ─────────────────────────────────────
  useEffect(() => {
    requestAnimationFrame(() =>
      requestAnimationFrame(() => setIsContentReady(true))
    );
  }, []);


  // ── Preload теории ─────────────────────────────────────
  async function preloadTheoryData() {
    const cacheKey = "global";
    if (theoryCache[cacheKey]) return theoryCache[cacheKey];

    const [rulesRes, tasksRes, typesRes] = await Promise.all([
      fetch(`/api/theory/all_theory`),
      fetch(`/api/theory/get_tasks_theory`),
      fetch(`/api/theory/all_theory_types`),
    ]);
    const data = {
      rules: await rulesRes.json(),
      tasks: await tasksRes.json(),
      types: await typesRes.json(),
    };
    setTheoryCache(prev => ({ ...prev, [cacheKey]: data }));
    return data;
  }


  async function navigateToPage(targetPage, { resetTask = false } = {}) {
    await performTransition(async () => {
      if (targetPage === "theory")   await preloadTheoryData();
      if (targetPage === "trainers") await loadTasks();
      setPage(targetPage);
      if (resetTask) setSelectedTask(null);
    });
  }


  // ── Header ────────────────────────────────────────────
  const header = (
    <div ref={title} className="mainTitle">
      <div className="mainTitle__picture" />
      <div className="mainTitle__title">PumRus</div>
      <div className="mainTitle__text">
        Супер крутой бот для подготовки к ЕГЭ. Йоу да свег супер топ МММ ++
        <br />
        <a href="https://github.com/dakdolka/pumrus" className="mainTitle__link">
          Узнать больше
        </a>
      </div>
    </div>
  );


  // ─────────────────────────────────────────────────────
  // СТРАНИЦЫ
  // ─────────────────────────────────────────────────────

  let content;

  // ── subject ───────────────────────────────────────────
  if (page === "subject") {
    content = (
      <>
        {header}
        <Chapter ref={day_task} func={() => navigateToPage("day-task")}>
          Ежедневное задание
        </Chapter>
        <Chapter ref={task} func={() => navigateToPage("trainers", { resetTask: true })}>
          Практика
        </Chapter>
        <Chapter ref={theory} func={() => navigateToPage("theory")}>
          Теория
        </Chapter>
        <Chapter ref={analysis} func={() => navigateToPage("analysis")}>
          Аналитика
        </Chapter>
      </>
    );
  }

  // ── day-task ──────────────────────────────────────────
  if (page === "day-task") {
    content = (
      <Chapter isValue="true" func={() => navigateToPage("subject")}>
        Ежедневное задание
      </Chapter>
    );
  }

  // ── trainers ──────────────────────────────────────────
  if (page === "trainers") {

    // Экран 1 — список заданий с группировкой
    if (!selectedTask) {
      content = (
        <>
          <div className="mainTitle">
            <div className="mainTitle__picture" />
            <div className="mainTitle__title">PumRus</div>
            <div className="mainTitle__text">Выберите задание для практики</div>
          </div>

          {tasksLoading && (
            <div className="task-select">
              <div className="task-select__spinner-wrap">
                <span className="task-select__spinner-inline" />
                <span>Загрузка...</span>
              </div>
            </div>
          )}

          {tasksError && (
            <div className="task-select">
              <div className="task-select__empty">{tasksError}</div>
            </div>
          )}

          {!tasksLoading && !tasksError && allTasks.length === 0 && (
            <div className="task-select">
              <div className="task-select__empty">Нет доступных заданий</div>
            </div>
          )}

          {!tasksLoading && !tasksError && allTasks.length > 0 && (
            <TaskSelect
              tasks={allTasks}
              onSelect={t => performTransition(() => setSelectedTask(t))}
            />
          )}
        </>
      );

    // Экран 2 — тренажёр
    } else {
      const storageKey = getStorageKey(
        selectedTask.task_group?.name ?? 'general',
        selectedTask.id
      );
      const onExit = () => performTransition(
        () => setSelectedTask(null),
        { withLoadingSpinner: false }
      );

      content = (
        <>
          <Chapter
            isValue="true"
            func={() => {
              if (trainerExitRef.current) trainerExitRef.current();
              else onExit();
            }}
          >
            {selectedTask.name}
          </Chapter>
          <UniversalTrainer
            task={selectedTask}
            userId={userId}
            storageKey={storageKey}
            onExit={onExit}
            exitRef={trainerExitRef}
          />
        </>
      );
    }
  }

  // ── theory ────────────────────────────────────────────
  if (page === "theory") {
    const cachedData = theoryCache["global"] || null;
    content = (
      <>
        <Chapter isValue="true" func={() => navigateToPage("subject")}>
          Теория
        </Chapter>
        <TheoryChoose
          preloadedRules={cachedData?.rules}
          preloadedTasks={cachedData?.tasks}
          availableTypes={cachedData?.types}
          isPopup={isTheoryPopupOpen}
          setPopup={setIsTheoryPopupOpen}
          content={theoryPopupContent}
          setContent={setTheoryPopupContent}
        />
        <Popup
          isPopup={isTheoryPopupOpen}
          setPopup={setIsTheoryPopupOpen}
          content={theoryPopupContent}
        />
      </>
    );
  }

  // ── analysis ──────────────────────────────────────────
  if (page === "analysis") {
    content = (
      <Chapter isValue="true" func={() => navigateToPage("subject")}>
        Аналитика
      </Chapter>
    );
  }


  return (
    <>
      <div className={`main ${isFadingOut ? "main--fading-out" : ""}`}>
        {isContentReady ? content : null}
      </div>
      {showLoadingIndicator && (
        <div className="loading-indicator">
          <div className="loading-spinner" />
          <div className="loading-text">Загрузка...</div>
        </div>
      )}
    </>
  );
}

export default App;
