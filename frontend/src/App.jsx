import { useRef, useState, useEffect } from "react";
import "./General.css";
import Chapter from "./components/Chapter/chapter.jsx";
import { Element, TaskElement, Popup } from "./components.jsx";
import { TaskSelect }        from "./components/trainers/TaskSelect.jsx";
import { UniversalTrainer }  from "./components/trainers/UniversalTrainer.jsx";
import { MistakesPage }      from "./components/mistakes/MistakesPage.jsx";
import { PracticeTrainer }   from "./components/mistakes/PracticeTrainer.jsx";
import { getStorageKey }     from "./components/trainers/trainerUtils.js";


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
      fetch(`/api/theory/all_theory`).then(r => r.json()).then(setRules).catch(console.error);
    }
  }, [preloadedRules]);

  useEffect(() => {
    if (!preloadedTasks) {
      fetch(`/api/theory/get_tasks_theory`).then(r => r.json()).then(setTasks).catch(console.error);
    }
  }, [preloadedTasks]);

  function handleSelect(id, isChoose) {
    setChosenBlock(prev =>
      isChoose ? (prev.includes(id) ? prev : [...prev, id]) : prev.filter(i => i !== id)
    );
  }

  useEffect(() => {
    if (chosenBlock.length === 0) {
      setViewRules(rules);
    } else {
      const filtered = [];
      rules.forEach(item => {
        (item.types || []).forEach(type => {
          if (chosenBlock.includes(type.id)) filtered.push(item);
        });
      });
      setViewRules(filtered);
    }
  }, [chosenBlock, rules]);

  function showContent(parent) {
    if (parent === "task") {
      setTaskMood(prev => !prev);
      if (isThemeActive) setThemeMood(false);
    } else {
      setThemeMood(prev => !prev);
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
        >Задания</div>
        <div
          ref={theme}
          className={isThemeActive
            ? "theoryChoose__elem theoryChoose__theme--active"
            : "theoryChoose__elem theoryChoose__theme--hidden"}
          onClick={() => showContent("theme")}
        >Темы</div>
      </div>

      <div className={isThemeActive
        ? "theoryChoose__block theoryChoose__block--active"
        : "theoryChoose__block--hidden"}
      >
        {(availableTypes || []).map(type => (
          <Option key={type.id} theme_id={type.id} onSelect={handleSelect}>
            {type.name}
          </Option>
        ))}
      </div>

      <div className={isThemeActive ? "elementBlock elementBlock--small" : "elementBlock elementBlock--big"}>
        {isTaskActive === false
          ? viewRules.map((item, index) => (
              <Element key={index} theory_id={item.id} setPopup={setPopup} setContent={setContent}>
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
  const task           = useRef();
  const theory         = useRef();
  const mistakes       = useRef();
  const title          = useRef();
  const trainerExitRef = useRef(null);

  const [userId,          setUserId]          = useState(null);
  const [selectedTask,    setSelectedTask]    = useState(null);
  const [allTasks,        setAllTasks]        = useState([]);
  const [tasksLoading,    setTasksLoading]    = useState(false);
  const [tasksError,      setTasksError]      = useState('');

  // Отработка ошибок
  const [practiceTask,     setPracticeTask]     = useState(null);
  const [practiceMistakes, setPracticeMistakes] = useState([]);
  const [mistakesRefresh,  setMistakesRefresh]  = useState(0);

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
      const all    = await fetch('/api/tasks/general/').then(r => r.json());
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

    const tgUser = tg.initDataUnsafe?.user;
    if (tgUser?.id) {
      fetch('/api/users/get-or-create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tg_id:       String(tgUser.id),
          name:        tgUser.first_name ?? 'User',
          second_name: tgUser.last_name  ?? '',
          username:    tgUser.username   ?? null,
          avatar_url:  null,
        }),
      })
        .then(r => r.json())
        .then(data => setUserId(data.user.id))
        .catch(console.error);
    }
  }, []);


  // ── Touch-эффекты ─────────────────────────────────────
  useEffect(() => {
    const onStart = e => { const b = e.target.closest("button"); if (b) b.classList.add("is-pressed"); };
    const onEnd   = e => { const b = e.target.closest("button"); if (b) setTimeout(() => b.classList.remove("is-pressed"), 270); };
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
    if (withLoadingSpinner) loadingTimer = setTimeout(() => setShowLoadingIndicator(true), 300);

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

      // Внутри тренажёра — обрабатывает UniversalTrainer
      if (page === "trainers" && selectedTask) return;

      // Внутри отработки ошибок
      if (page === "mistakes" && practiceTask) {
        await performTransition(() => {
          setPracticeTask(null);
          setPracticeMistakes([]);
        }, { withLoadingSpinner: false });
        return;
      }

      const backMap = {
        theory:   "subject",
        trainers: "subject",
        mistakes: "subject",
      };

      const targetPage = backMap[page];
      if (!targetPage) { tg.close?.(); return; }

      await performTransition(() => {
        setPage(targetPage);
        if (targetPage === "subject") {
          setSelectedTask(null);
          setPracticeTask(null);
          setPracticeMistakes([]);
        }
      }, { withLoadingSpinner: false });
    };

    if (["subject", "theory", "trainers", "mistakes"].includes(page)) {
      tg.BackButton.show();
      tg.onEvent("backButtonClicked", handleBack);
    } else {
      tg.BackButton.hide();
    }

    return () => tg.offEvent?.("backButtonClicked", handleBack);
  }, [page, isTheoryPopupOpen, selectedTask, practiceTask]);


  // ── Первый рендер ─────────────────────────────────────
  useEffect(() => {
    requestAnimationFrame(() => requestAnimationFrame(() => setIsContentReady(true)));
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

  async function navigateToPage(targetPage, opts = {}) {
    await performTransition(async () => {
      if (targetPage === "theory")   await preloadTheoryData();
      if (targetPage === "trainers") await loadTasks();
      setPage(targetPage);
      if (opts.resetTask) setSelectedTask(null);
    });
  }


  // ── Header ────────────────────────────────────────────
  const header = (
    <div ref={title} className="mainTitle">
      <div className="mainTitle__picture" />
      <div className="mainTitle__text">
        Супер крутой бот для подготовки к ЕГЭ :)
        <br />
        <a href="https://github.com/dakdolka/pumrus" className="mainTitle__link">Узнать больше</a>
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
        <Chapter ref={theory} func={() => navigateToPage("theory")}>
          Теория
        </Chapter>
        <Chapter ref={task} func={() => navigateToPage("trainers", { resetTask: true })}>
          Практика
        </Chapter>
        <Chapter ref={mistakes} func={() => navigateToPage("mistakes")}>
          Ошибки
        </Chapter>
      </>
    );
  }

  // ── mistakes ──────────────────────────────────────────
  if (page === "mistakes") {

    // Режим отработки — внутри страницы ошибок
    if (practiceTask) {
      content = (
        <>
          <Chapter
            isValue="true"
            func={() => performTransition(() => {
              setPracticeTask(null);
              setPracticeMistakes([]);
            }, { withLoadingSpinner: false })}
          >
            {practiceTask.name}
          </Chapter>
          <PracticeTrainer
            task={practiceTask}
            mistakes={practiceMistakes}
            userId={userId}
            onExit={() => performTransition(() => {
              setPracticeTask(null);
              setPracticeMistakes([]);
            }, { withLoadingSpinner: false })}
            onResolved={() => setMistakesRefresh(r => r + 1)}
          />
        </>
      );

    // Обычный режим — список ошибок
    } else {
      content = (
        <>
          <Chapter
            isValue="true"
            func={() => navigateToPage("subject")}
          >
            Ошибки
          </Chapter>
          <MistakesPage
            userId={userId}
            refreshKey={mistakesRefresh}
            onStartPractice={(t, ms) => performTransition(() => {
              setPracticeTask(t);
              setPracticeMistakes(ms);
            }, { withLoadingSpinner: false })}
          />
        </>
      );
    }
  }

  // ── trainers ──────────────────────────────────────────
  if (page === "trainers") {

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

    } else {
      const storageKey = getStorageKey(selectedTask.task_group?.name ?? 'general', selectedTask.id);
      const onExit     = () => performTransition(() => setSelectedTask(null), { withLoadingSpinner: false });

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
