import { useRef, useState, useEffect } from "react";
import "./General.css";
import Chapter from "./components/Chapter/chapter.jsx";
import { Element, TaskElement, Popup } from "./components.jsx";
import { StressTrainer }     from "./components/trainers/StressTrainer.jsx";
import { PrefixTrainer }     from "./components/trainers/PrefixTrainer.jsx";
import { DictionaryTrainer } from "./components/trainers/DictionaryTrainer.jsx";
import { SpellingTrainer }   from "./components/trainers/SpellingTrainer.jsx";
import { TaskSelect }        from "./components/trainers/TaskSelect.jsx";
import { adaptItems, getStorageKey } from "./components/trainers/trainerUtils.js";


// Маппинг trainer_type → компонент и лейбл
// Это единственная "статика" — она неизбежна, т.к. компоненты это код
const TRAINER_META = {
  stress:     { label: "Орфоэпия",           Component: StressTrainer },
  prefix:     { label: "ПРЕ/ПРИ",            Component: PrefixTrainer },
  dictionary: { label: "Словарные слова",    Component: DictionaryTrainer },
  spelling:   { label: "Слитно / Раздельно", Component: SpellingTrainer },
};

// Порядок отображения типов
const TRAINER_ORDER = ["stress", "prefix", "dictionary", "spelling"];


function saveInfo(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getInfo(key) {
  return JSON.parse(localStorage.getItem(key));
}


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


function TheoryChoose({ preloadedRules, preloadedTasks, isPopup, setPopup, content, setContent }) {
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
      />

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


function App() {
  const day_task  = useRef();
  const task      = useRef();
  const theory    = useRef();
  const analysis  = useRef();
  const title     = useRef();
  const trainerExitRef = useRef(null);

  const [selectedTrainerType, setSelectedTrainerType] = useState(null); // "stress" | "prefix" | ...
  const [selectedTask,        setSelectedTask]        = useState(null); // полная задача с items
  const [availableTrainers,   setAvailableTrainers]   = useState([]);   // [{type, label, tasks[]}]
  const [trainersLoading,     setTrainersLoading]     = useState(false);
  const [trainersError,       setTrainersError]       = useState('');

  const [isFadingOut,          setIsFadingOut]          = useState(false);
  const [showLoadingIndicator, setShowLoadingIndicator] = useState(false);
  const [isContentReady,       setIsContentReady]       = useState(false);
  const [theoryCache,          setTheoryCache]          = useState({});
  const [page,                 setPage]                 = useState("subject");

  const [isTheoryPopupOpen,  setIsTheoryPopupOpen]  = useState(false);
  const [theoryPopupContent, setTheoryPopupContent] = useState({ title: "Отсутствует", blocks: [] });


  function clearTrainer() {
    setSelectedTrainerType(null);
    setSelectedTask(null);
  }


  // Загрузка и группировка задач при входе на страницу тренажёров
  async function loadTrainers() {
    setTrainersLoading(true);
    setTrainersError('');
    try {
      const all = await fetch('/api/tasks/').then(r => r.json());

      // Группируем активные задачи по trainer_type, сохраняем порядок TRAINER_ORDER
      const grouped = {};
      all
        .filter(t => t.is_active)
        .forEach(t => {
          if (!grouped[t.trainer_type]) grouped[t.trainer_type] = [];
          grouped[t.trainer_type].push(t);
        });

      const result = TRAINER_ORDER
        .filter(type => grouped[type]?.length > 0 && TRAINER_META[type])
        .map(type => ({
          type,
          label: TRAINER_META[type].label,
          tasks: grouped[type],
        }));

      setAvailableTrainers(result);
    } catch {
      setTrainersError('Не удалось загрузить задания');
    } finally {
      setTrainersLoading(false);
    }
  }


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
  }, []);


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


  async function performTransition(action, { withLoadingSpinner = true } = {}) {
    setIsFadingOut(true);
    await new Promise((resolve) => setTimeout(resolve, 300));

    setIsContentReady(false);

    let loadingTimer;
    if (withLoadingSpinner) {
      loadingTimer = setTimeout(() => setShowLoadingIndicator(true), 300);
    }

    await action?.();
    await new Promise((resolve) => setTimeout(resolve, 50));

    setIsContentReady(true);
    await new Promise((resolve) => {
      requestAnimationFrame(() =>
        requestAnimationFrame(() => setTimeout(resolve, 50))
      );
    });

    clearTimeout(loadingTimer);
    setShowLoadingIndicator(false);
    setIsFadingOut(false);
  }


  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    const backButton = tg.BackButton;

    const handleBack = async () => {
      setShowLoadingIndicator(false);

      if (isTheoryPopupOpen) { setIsTheoryPopupOpen(false); return; }

      // Тренажёр запущен — хук тренажёра сам обрабатывает
      if (page === "trainers" && selectedTrainerType && selectedTask) return;

      // Экран выбора задачи → назад к выбору типа
      if (page === "trainers" && selectedTrainerType && !selectedTask) {
        await performTransition(() => setSelectedTrainerType(null), { withLoadingSpinner: false });
        return;
      }

      const backMap = {
        theory:    "subject",
        trainers:  "subject",
        analysis:  "subject",
        "day-task": "subject",
      };

      const targetPage = backMap[page];
      if (!targetPage) { tg.close?.(); return; }

      await performTransition(() => setPage(targetPage), { withLoadingSpinner: false });
    };

    if (["subject", "theory", "trainers", "analysis", "day-task"].includes(page)) {
      backButton.show();
      tg.onEvent("backButtonClicked", handleBack);
    } else {
      backButton.hide();
    }

    return () => tg.offEvent?.("backButtonClicked", handleBack);
  }, [page, isTheoryPopupOpen, selectedTrainerType, selectedTask]);


  useEffect(() => {
    requestAnimationFrame(() =>
      requestAnimationFrame(() => setIsContentReady(true))
    );
  }, []);


  async function preloadTheoryData() {
    const cacheKey = "global";
    if (theoryCache[cacheKey]) return theoryCache[cacheKey];

    const [rulesRes, tasksRes] = await Promise.all([
      fetch(`/api/theory/all_theory`),
      fetch(`/api/theory/get_tasks_theory`),
    ]);
    const rules = await rulesRes.json();
    const tasks = await tasksRes.json();
    const data  = { rules, tasks };

    setTheoryCache((prev) => ({ ...prev, [cacheKey]: data }));
    return data;
  }


  async function navigateToPage(targetPage, { resetTrainer = false } = {}) {
    await performTransition(async () => {
      const t0 = performance.now();
      if (targetPage === "theory")   await preloadTheoryData();
      if (targetPage === "trainers") await loadTrainers();
      setPage(targetPage);
      if (resetTrainer) clearTrainer();
      console.log(`⏱️ Время подготовки: ${(performance.now() - t0).toFixed(2)}ms`);
    });
  }


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


  let content;

  if (page === "subject") {
    content = (
      <>
        {header}
        <Chapter ref={day_task} func={() => navigateToPage("day-task")}>
          Ежедневное задание
        </Chapter>
        <Chapter ref={task} func={() => navigateToPage("trainers", { resetTrainer: true })}>
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

  if (page === "day-task") {
    content = (
      <Chapter isValue="true" func={() => navigateToPage("subject")}>
        Ежедневное задание
      </Chapter>
    );
  }

  if (page === "trainers") {
    if (!selectedTrainerType) {
      // Шаг 1: выбор типа тренажёра — список из API
      content = (
        <>
          <div className="mainTitle">
            <div className="mainTitle__picture" />
            <div className="mainTitle__title">PumRus</div>
            <div className="mainTitle__text">Выберите тренажёр для практики</div>
          </div>

          {trainersLoading && (
            <div className="task-select">
              <div className="task-select__spinner-wrap">
                <span className="task-select__spinner-inline" />
                <span>Загрузка...</span>
              </div>
            </div>
          )}

          {trainersError && (
            <div className="task-select">
              <div className="task-select__empty">{trainersError}</div>
            </div>
          )}

          {!trainersLoading && !trainersError && (
            <div className="subject__block">
              {availableTrainers.map(({ type, label }) => (
                <Chapter
                  key={type}
                  subject={false}
                  func={() => performTransition(() => setSelectedTrainerType(type))}
                >
                  {label}
                </Chapter>
              ))}
            </div>
          )}
        </>
      );

    } else if (!selectedTask) {
      // Шаг 2: выбор задания — список из кэша, без нового запроса
      const current = availableTrainers.find(t => t.type === selectedTrainerType);
      content = (
        <>
          <Chapter
            isValue="true"
            func={() => performTransition(() => setSelectedTrainerType(null), { withLoadingSpinner: false })}
          >
            {current?.label}
          </Chapter>
          <TaskSelect
            tasks={current?.tasks || []}
            trainerLabel={current?.label}
            onSelect={fullTask => performTransition(() => setSelectedTask(fullTask))}
          />
        </>
      );

    } else {
      // Шаг 3: прохождение тренажёра
      const meta       = TRAINER_META[selectedTrainerType];
      const rawData    = adaptItems(selectedTrainerType, selectedTask.items || []);
      const storageKey = getStorageKey(selectedTrainerType, selectedTask.id);
      const onExit     = () => performTransition(() => setSelectedTask(null), { withLoadingSpinner: false });

      content = (
        <>
          <Chapter
            isValue="true"
            func={() => {
              if (trainerExitRef.current) trainerExitRef.current();
              else performTransition(() => setSelectedTask(null));
            }}
          >
            {selectedTask.name}
          </Chapter>
          <meta.Component
            onExit={onExit}
            exitRef={trainerExitRef}
            rawData={rawData}
            storageKey={storageKey}
          />
        </>
      );
    }
  }

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
