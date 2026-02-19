import { useRef, useState, useEffect } from 'react'
import './General.css'
import Chapter from './components/Chapter/chapter.jsx'
import { Element, TaskElement, Popup } from './components.jsx'
import { StressTrainer }     from './components/trainers/StressTrainer.jsx'
import { PrefixTrainer }     from './components/trainers/PrefixTrainer.jsx'
import { DictionaryTrainer } from './components/trainers/DictionaryTrainer.jsx'
import { SpellingTrainer }   from './components/trainers/SpellingTrainer.jsx'


function saveInfo(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getInfo(key) {
  return JSON.parse(localStorage.getItem(key));
}

// ─── Конфиг тренажёров ────────────────────────────────────────────────────────
// Чтобы добавить новый — просто добавь сюда объект, больше ничего менять не надо
const TRAINERS = [
  { id: 'stress',   label: 'Орфоэпия',         Component: StressTrainer     },
  { id: 'prefix',   label: 'ПРЕ/ПРИ',           Component: PrefixTrainer     },
  { id: 'dict',     label: 'Словарные слова',    Component: DictionaryTrainer },
  { id: 'spelling', label: 'Слитно / Раздельно', Component: SpellingTrainer   },
];


function Option({ children, onSelect, theme_id }) {
  const [isChosen, setMood] = useState(false);

  return (
    <div
      className="option"
      data-ischosen={isChosen.toString()}
      onClick={() => {
        setMood(prev => {
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
  object,
  preloadedRules,
  preloadedTasks,
  isPopup,
  setPopup,
  content,
  setContent,
}) {
  console.log("-----< Полученный предмет >-----", object);

  const task  = useRef();
  const theme = useRef();

  const [isTaskActive,  setTaskMood]  = useState(false);
  const [isThemeActive, setThemeMood] = useState(false);

  const [chosenBlock, setChosenBlock] = useState([]);
  const [viewRules,   setViewRules]   = useState([]);
  const [rules, setRules] = useState(preloadedRules || []);
  const [tasks, setTasks] = useState(preloadedTasks || []);

  useEffect(() => {
    if (!preloadedRules) {
      fetch(`/api/theory/all_theory_for_subject/${object.id}`)
        .then(r => r.json())
        .then(setRules);
    }
  }, [object.id, preloadedRules]);

  useEffect(() => {
    if (!preloadedTasks) {
      fetch(`/api/theory/get_tasks_theory_for_subject/${object.id}`)
        .then(r => r.json())
        .then(setTasks);
    }
  }, [object.id, preloadedTasks]);

  console.log("-----< Правила >-----", rules);

  function handleSelect(id, isChoose) {
    setChosenBlock(prev =>
      isChoose
        ? prev.includes(id) ? prev : [...prev, id]
        : prev.filter(item => item !== id)
    );
  }

  useEffect(() => {
    if (chosenBlock.length === 0) {
      setViewRules(rules);
    } else {
      const filtered = [];
      rules.forEach(item => {
        item.types.forEach(type => {
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
        {object.types.map((item, index) => (
          <Option key={index} onSelect={handleSelect} theme_id={item.id}>
            {item.name}
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
            ))}
      </div>
    </>
  );
}


function App() {
  const day_task = useRef();
  const task     = useRef();
  const theory   = useRef();
  const analysis = useRef();
  const title    = useRef();

  const [subjects,      getSubjects]      = useState([]);
  const [object,        chooseSubject]    = useState();
  const [selectedTrainer, setSelectedTrainer] = useState(null);
  const [isFadingOut,         setIsFadingOut]         = useState(false);
  const [showLoadingIndicator, setShowLoadingIndicator] = useState(false);
  const [isContentReady,      setIsContentReady]      = useState(false);
  const [theoryCache,         setTheoryCache]         = useState({});
  const [page,                setPage]                = useState("main");

  const [isTheoryPopupOpen,   setIsTheoryPopupOpen]   = useState(false);
  const [theoryPopupContent,  setTheoryPopupContent]  = useState({
    title: "Отсутствует",
    blocks: [],
  });

  useEffect(() => {
    fetch("/api/theory/all_theory_dop_info")
      .then(r => r.json())
      .then(data => {
        getSubjects(data);
        console.log("-----< Полученные предметы >-----", data);
      });
  }, []);

  useEffect(() => {
    const tg = window.Telegram?.WebApp || {};
    tg.ready?.();
    tg.expand?.();

    const params      = tg.themeParams || {};
    const isDark      = tg.colorScheme === 'dark';
    const root        = document.documentElement;
    const setVar      = (name, value) => { if (value) root.style.setProperty(`--${name}`, value); };

    document.body.classList.toggle('theme--light', !isDark);
    document.body.classList.toggle('theme--dark',   isDark);

    setVar('text-color',  params.text_color);
    setVar('main-color',  params.bg_color);
    setVar('block-color', params.secondary_bg_color || params.section_bg_color);

    const accent = isDark ? 'rgb(255, 200, 100)' : (params.header_bg_color || '#3b6fd4');
    const mix    = isDark ? '10%' : '7%';
    setVar('active-color', accent);
    root.style.setProperty('--rule-color', `color-mix(in srgb, ${accent} ${mix}, transparent)`);
  }, []);

  // ─── Единый хелпер анимированного перехода ──────────────────────────────────
  // action — async-функция с логикой конкретного перехода (setPage, setSelectedTrainer и т.д.)
  async function performTransition(action, { withLoadingSpinner = true } = {}) {
    setIsFadingOut(true);
    await new Promise(resolve => setTimeout(resolve, 300));

    setIsContentReady(false);

    let loadingTimer;
    if (withLoadingSpinner) {
      loadingTimer = setTimeout(() => setShowLoadingIndicator(true), 300);
    }

    await action?.();
    await new Promise(resolve => setTimeout(resolve, 50));

    setIsContentReady(true);
    await new Promise(resolve => {
      requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve, 50)));
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

      // 1) Закрыть попап теории
      if (isTheoryPopupOpen) {
        setIsTheoryPopupOpen(false);
        return;
      }

      // 2) Вернуться из конкретного тренажёра к списку
      if (page === 'trainers' && selectedTrainer) {
        return;
      }

      // 3) Обычная страничная навигация назад
      const backMap = {
        theory:    'subject',
        trainers:  'subject',
        analysis:  'subject',
        'day-task': 'subject',
        subject:   'main',
      };

      const targetPage = backMap[page];
      if (!targetPage) {
        tg.close?.();
        return;
      }

      await performTransition(() => setPage(targetPage), { withLoadingSpinner: false });
    };

    if (['subject', 'theory', 'trainers', 'analysis', 'day-task'].includes(page)) {
      backButton.show();
      tg.onEvent('backButtonClicked', handleBack);
    } else {
      backButton.hide();
    }

    return () => tg.offEvent?.('backButtonClicked', handleBack);
  }, [page, isTheoryPopupOpen, selectedTrainer]);

  useEffect(() => {
    requestAnimationFrame(() => requestAnimationFrame(() => setIsContentReady(true)));
  }, []);

  async function preloadTheoryData(objectId) {
    console.log(`📥 Предзагрузка данных для theory, object.id: ${objectId}`);
    if (theoryCache[objectId]) {
      console.log(`✅ Данные уже в кэше`);
      return theoryCache[objectId];
    }

    const [rulesRes, tasksRes] = await Promise.all([
      fetch(`/api/theory/all_theory_for_subject/${objectId}`),
      fetch(`/api/theory/get_tasks_theory_for_subject/${objectId}`),
    ]);
    const rules = await rulesRes.json();
    const tasks = await tasksRes.json();
    const data  = { rules, tasks };

    setTheoryCache(prev => ({ ...prev, [objectId]: data }));
    console.log(`✅ Данные загружены и закэшированы`);
    return data;
  }

  async function navigateToPage(targetPage, { resetTrainer = false } = {}) {
    console.log(`🚀 Переход на: ${targetPage}`);

    await performTransition(async () => {
      const t0 = performance.now();
      if (targetPage === 'theory' && object) await preloadTheoryData(object.id);
      setPage(targetPage);
      if (resetTrainer) setSelectedTrainer(null);
      console.log(`⏱️ Время подготовки: ${(performance.now() - t0).toFixed(2)}ms`);
    });

    console.log(`✅ Переход завершён: ${targetPage}`);
  }

  // ─── Шапка (повторяется на main и subject) ──────────────────────────────────
  const header = (
    <div ref={title} className="mainTitle">
      <div className="mainTitle__picture" />
      <div className="mainTitle__title">PumRus</div>
      <div className="mainTitle__text">
        Супер крутой бот для подготовки к ЕГЭ. Йоу да свег супер топ МММ ++
        <br />
        <a href="https://github.com/dakdolka/pumrus" className="mainTitle__link">Узнать больше</a>
      </div>
    </div>
  );

  // ─── Рендер страниц ──────────────────────────────────────────────────────────
  let content;

  if (page === "main") {
    content = (
      <>
        {header}
        <div className="subject__block">
          {subjects.map((item, index) => (
            <Chapter
              key={index}
              subject="true"
              func={() => {
                chooseSubject(item);
                navigateToPage("subject");
                console.log("------< Предмет >------", item.subject);
              }}
            >
              {item.subject}
            </Chapter>
          ))}
        </div>
      </>
    );
  }

  if (page === "subject") {
    content = (
      <>
        {header}
        <Chapter ref={day_task} func={() => navigateToPage("day-task")}>Ежедневное задание</Chapter>
        <Chapter ref={task}     func={() => navigateToPage("trainers", { resetTrainer: true })}>Практика</Chapter>
        <Chapter ref={theory}   func={() => navigateToPage("theory")}>Теория</Chapter>
        <Chapter ref={analysis} func={() => navigateToPage("analysis")}>Аналитика</Chapter>
        <div className="back-to-subjects-button" onClick={() => navigateToPage("main")} />
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
    if (!selectedTrainer) {
      content = (
        <>
          <div className="mainTitle">
            <div className="mainTitle__picture" />
            <div className="mainTitle__title">PumRus</div>
            <div className="mainTitle__text">Выберите тренажёр для практики</div>
          </div>

          <div className="subject__block">
            {TRAINERS.map(({ id, label }) => (
              <Chapter
                key={id}
                subject={false}
                func={() => performTransition(() => setSelectedTrainer(id))}
              >
                {label}
              </Chapter>
            ))}
          </div>

          <div className="back-to-subjects-button" onClick={() => navigateToPage('subject')} />
        </>
      );
    } else {
      const trainer = TRAINERS.find(t => t.id === selectedTrainer);

      content = (
        <>
          <Chapter
            isValue="true"
            func={() => performTransition(() => setSelectedTrainer(null))}
          >
            {trainer?.label}
          </Chapter>

          {trainer?.Component && (
            <trainer.Component
              onExit={() => performTransition(() => setSelectedTrainer(null), { withLoadingSpinner: false })}
            />
          )}
        </>
      );
    }
  }

  if (page === "theory") {
    const cachedData = object ? theoryCache[object.id] : null;
    content = (
      <>
        <Chapter isValue="true" func={() => navigateToPage("subject")}>Теория</Chapter>
        <TheoryChoose
          object={object}
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
      <div className={`main ${isFadingOut ? 'main--fading-out' : ''}`}>
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
