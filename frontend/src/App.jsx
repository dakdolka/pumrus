import { useRef, useState, useEffect } from 'react'
import './General.css'
import Chapter from './components/Chapter/chapter.jsx'
import { Element, TaskElement, Popup } from './components.jsx'
import { StressTrainer } from './components/trainers/StressTrainer.jsx'
import { PrefixTrainer } from './components/trainers/PrefixTrainer.jsx'
import { DictionaryTrainer } from './components/trainers/DictionaryTrainer.jsx'

function saveInfo(key, value) {
    const jsonString = JSON.stringify(value);
    localStorage.setItem(key, jsonString);
}

function getInfo(key) {
    const jsonString = localStorage.getItem(key);
    return JSON.parse(jsonString);
}

function Option({ children, onSelect, theme_id }) {
  const [isChosen, setMood] = useState(false);

  return (
    <div className="option" data-ischosen={isChosen.toString()} onClick={() => {
        setMood(prev => {
          onSelect(theme_id, !prev);
          return !prev
        })
      }}>
      <div className={isChosen ? "option__button option__button--active" : "option__button"}></div>
      <div className="option__nameBlock">
        <div className="option__name">{children}</div>
      </div>
    </div>
  )
}

function TheoryChoose({ object, preloadedRules, preloadedTasks }) {
  console.log("-----< Полученный предмет >-----", object);

  const task = useRef();
  const theme = useRef();

  const [isPopup, setPopup] = useState(false);
  const [content, setContent] = useState({
    title: "Отсутствует",
    blocks: [],
  });

  const [isTaskActive, setTaskMood] = useState(false);
  const [isThemeActive, setThemeMood] = useState(false);

  const [chosenBlock, setChosenBlock] = useState([]);

  const [viewRules, setViewRules] = useState([]);
  
  // 🆕 Используем предзагруженные данные или загружаем
  const [rules, setRules] = useState(preloadedRules || []);
  const [tasks, setTasks] = useState(preloadedTasks || []);
  
  useEffect(() => {
    // Если данные не были предзагружены, загружаем
    if (!preloadedRules) {
      fetch(`/api/theory/all_theory_for_subject/${object.id}`)
        .then(response => response.json())
        .then(data => {
          setRules(data)
      })
    }
  }, [object.id, preloadedRules]);

  useEffect(() => {
    if (!preloadedTasks) {
      fetch(`/api/theory/get_tasks_theory_for_subject/${object.id}`)
        .then(response => response.json())
        .then(data => {
          setTasks(data)
        })
    }
  }, [object.id, preloadedTasks]);

  console.log("-----< Правила >-----", rules);

  function handleSelect(id, isChoose) {
    setChosenBlock(prev => {
      if (isChoose) {
        if (!prev.includes(id)) return [...prev, id];
        return prev;
      } else {
        return prev.filter(item => item !== id);
      }
    });
  };

  useEffect(() => {
    if (chosenBlock.length === 0) {
      setViewRules(rules);
    } else {
      setViewRules([]);
      rules.map(item => {
        item.types.map(type => {
          if (chosenBlock.includes(type.id)) {
            setViewRules(prev => [...prev, item]);
          }
        })
      })
    }
  }, [chosenBlock, rules]);  

  function showContent(parent) {
    if (parent === "task") {
      setTaskMood(!isTaskActive);
      if (isThemeActive) {
        setThemeMood(false);
      }
    } else {
      setThemeMood(!isThemeActive);
      if (isTaskActive) {
        setTaskMood(false);
      }
    }
  }
  
  return (
    <>
      <div className="theoryChoose">
        <div ref={task} className={isTaskActive ? "theoryChoose__elem theoryChoose__task--active" : "theoryChoose__elem theoryChoose__task--hidden"} onClick={() => showContent("task")}>Задания</div>
        <div ref={theme} className={isThemeActive ? "theoryChoose__elem theoryChoose__theme--active" : "theoryChoose__elem theoryChoose__theme--hidden"} onClick={() => showContent("theme")}>Темы</div>
      </div>
      <div className={isThemeActive ? "theoryChoose__block theoryChoose__block--active" : "theoryChoose__block--hidden"}>
        {object.types.map((item, index) => {
          return (
            <Option key={index} onSelect={handleSelect} theme_id={item.id}>{item.name}</Option>
          )
        })}
      </div>
      <div className={isThemeActive ? "elementBlock elementBlock--small" : "elementBlock elementBlock--big"}>
        {isTaskActive === false 
        ? viewRules.map((item, index) => {
          return (
            <Element key={index} theory_id={item.id} setPopup={setPopup} setContent={setContent}>{item.name}</Element>
          )
        })
        : tasks.map((item, index) => {
          return (
            <TaskElement key={index} is_single={item.is_single} content={item.tasks} setPopup={setPopup} setContent={setContent}>{item.group_name}</TaskElement>
          )
        })}
      </div>
      <Popup isPopup={isPopup} setPopup={setPopup} content={content}/>
    </>
  )
}

function App() {
  const day_task = useRef();
  const task = useRef();
  const theory = useRef();
  const analysis = useRef();
  const title = useRef();

  const [subjects, getSubjects] = useState([]);
  const [object, chooseSubject] = useState();
  const [selectedTrainer, setSelectedTrainer] = useState(null);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [showLoadingIndicator, setShowLoadingIndicator] = useState(false);
  const [isContentReady, setIsContentReady] = useState(false);

  // 🆕 Кэш для предзагрузки данных theory
  const [theoryCache, setTheoryCache] = useState({});

  useEffect(() => {
    fetch("/api/theory/all_theory_dop_info")
      .then(response => response.json())
      .then(data => {
        getSubjects(data)
        console.log("-----< Полученные предметы >-----", data)
      })
  }, []);

  const [page, setPage] = useState("main");

  useEffect(() => {
    const tg = window.Telegram?.WebApp || {};
    tg.ready?.();
    tg.expand?.();

    const params = tg.themeParams || {};
    const colorScheme = tg.colorScheme; // 'light' | 'dark' | undefined
    const isDark = colorScheme === 'dark';

    document.body.classList.toggle('theme--light', !isDark);
    document.body.classList.toggle('theme--dark', isDark);

    const root = document.documentElement;
    const setVar = (name, value) => {
      if (value) root.style.setProperty(`--${name}`, value);
    };

    // Общие цвета из Telegram
    setVar('text-color', params.text_color);
    setVar('main-color', params.bg_color);
    setVar('block-color', params.secondary_bg_color || params.section_bg_color);

    if (isDark) {
      // ТЁМНАЯ ТЕМА — твой жёлтый акцент
      const accent = 'rgb(255, 200, 100)';
      setVar('active-color', accent);
      root.style.setProperty(
        '--rule-color',
        `color-mix(in srgb, ${accent} 10%, transparent)`
      );
    } else {
      // СВЕТЛАЯ ТЕМА — телеграммовский синий (или твой запасной)
      const accent = params.header_bg_color || '#3b6fd4';
      setVar('active-color', accent);
      root.style.setProperty(
        '--rule-color',
        `color-mix(in srgb, ${accent} 7%, transparent)`
      );
    }
  }, []);

  



  // При первом монтировании
  useEffect(() => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setIsContentReady(true);
      });
    });
  }, []);

  // 🆕 ПРЕДЗАГРУЗКА ДАННЫХ ДЛЯ THEORY
  async function preloadTheoryData(objectId) {
    console.log(`📥 Предзагрузка данных для theory, object.id: ${objectId}`);
    
    // Проверяем кэш
    if (theoryCache[objectId]) {
      console.log(`✅ Данные уже в кэше`);
      return theoryCache[objectId];
    }
    
    // Загружаем параллельно
    const [rulesResponse, tasksResponse] = await Promise.all([
      fetch(`/api/theory/all_theory_for_subject/${objectId}`),
      fetch(`/api/theory/get_tasks_theory_for_subject/${objectId}`)
    ]);
    
    const rules = await rulesResponse.json();
    const tasks = await tasksResponse.json();
    
    const data = { rules, tasks };
    
    // Сохраняем в кэш
    setTheoryCache(prev => ({
      ...prev,
      [objectId]: data
    }));
    
    console.log(`✅ Данные загружены и закэширован`);
    return data;
  }

  // 🔥 ЕДИНАЯ ФУНКЦИЯ ПЕРЕХОДА
  async function navigateToPage(targetPage, additionalActions = {}) {
    console.log(`🚀 Переход на: ${targetPage}`);
    
    // 1. Fade-out
    setIsFadingOut(true);
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // 2. Скрываем контент
    setIsContentReady(false);
    
    // 3. Таймер для индикатора загрузки (только если долго)
    const loadingTimer = setTimeout(() => {
      setShowLoadingIndicator(true);
      console.log('⏳ Показываем индикатор загрузки...');
    }, 300); // 🆕 Увеличили до 300ms
    
    const renderStartTime = performance.now();
    
    // 4. 🆕 ДЛЯ THEORY ПРЕДЗАГРУЖАЕМ ДАННЫЕ
    if (targetPage === 'theory' && object) {
      await preloadTheoryData(object.id);
    }
    
    // 5. Меняем страницу
    setPage(targetPage);
    if (additionalActions.resetTrainer) {
      setSelectedTrainer(null);
    }
    
    // 6. Минимальная задержка для рендера
    await new Promise(resolve => setTimeout(resolve, 50));
    
    const renderTime = performance.now() - renderStartTime;
    console.log(`⏱️ Время подготовки: ${renderTime.toFixed(2)}ms`);
    
    // 7. Показываем контент
    setIsContentReady(true);
    
    // 8. Стабилизация
    await new Promise(resolve => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setTimeout(resolve, 50);
        });
      });
    });
    
    // 9. Убираем индикатор и делаем fade-in
    clearTimeout(loadingTimer);
    setShowLoadingIndicator(false);
    setIsFadingOut(false);
    
    console.log(`✅ Переход завершён: ${targetPage}`);
  }

  let content;
  
  if (page === "main") {
    content =
    <>
    <div ref={title} className="mainTitle">
      <div className="mainTitle__picture" />
      <div className="mainTitle__title">PumRus</div>
      <div className="mainTitle__text">
        Супер крутой бот для подготовки к ЕГЭ. Йоу да свег супер топ МММ ++
        <br />
        <a href="https://github.com/dakdolka/pumrus" className="mainTitle__link">Узнать больше</a>
      </div>
    </div>
    <div className="subject__block">
      {subjects.map((item, index) => {
        return (
          <Chapter 
            key={index}
            subject="true"
            func={() => {
              chooseSubject(item);
              navigateToPage("subject");
              console.log("------< Предмет >------", item.subject)
            }}
          >
            {item.subject}
          </Chapter>
        )
      })}
    </div>
    </>
  }
  
  if (page === "subject") {
    content = 
      <>
        <div ref={title} className="mainTitle">
          <div className="mainTitle__picture" />
          <div className="mainTitle__title">PumRus</div>
          <div className="mainTitle__text">
            Супер крутой бот для подготовки к ЕГЭ. Йоу да свег супер топ МММ ++
            <br />
            <a href="https://github.com/dakdolka/pumrus" className="mainTitle__link">Узнать больше</a>
          </div>
        </div>
        <Chapter 
          ref={day_task} 
          func={() => navigateToPage("day-task")}
        >
          Ежедневное задание
        </Chapter>
        <Chapter 
          ref={task} 
          func={() => navigateToPage("trainers", { resetTrainer: true })}
        >
          Практика
        </Chapter>
        <Chapter 
          ref={theory} 
          func={() => navigateToPage("theory")}
        >
          Теория
        </Chapter>
        <Chapter 
          ref={analysis} 
          func={() => navigateToPage("analysis")}
        >
          Аналитика
        </Chapter>
        <div 
          className="back-to-subjects-button" 
          onClick={() => navigateToPage("main")}
        />
      </>
  }

  if (page === "day-task") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => navigateToPage("subject")}
        >
          Ежедневное задание
        </Chapter>
      </>
    )
  }

  if (page === "trainers") {
    if (!selectedTrainer) {
      content = (
        <>
          <div className="mainTitle">
            <div className="mainTitle__picture" />
            <div className="mainTitle__title">PumRus</div>
            <div className="mainTitle__text">
              Выберите тренажёр для практики
            </div>
          </div>
          
          <div className="subject__block">
            <Chapter 
              subject={false}
              func={async () => {
                setIsFadingOut(true);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                setIsContentReady(false);
                
                const loadingTimer = setTimeout(() => {
                  setShowLoadingIndicator(true);
                }, 300);
                
                setSelectedTrainer('stress');
                await new Promise(resolve => setTimeout(resolve, 50));
                
                setIsContentReady(true);
                await new Promise(resolve => {
                  requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                      setTimeout(resolve, 50);
                    });
                  });
                });
                
                clearTimeout(loadingTimer);
                setShowLoadingIndicator(false);
                setIsFadingOut(false);
              }}
            >
              Орфоэпия (ударения)
            </Chapter>
            
            <Chapter 
              subject={false}
              func={async () => {
                setIsFadingOut(true);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                setIsContentReady(false);
                
                const loadingTimer = setTimeout(() => {
                  setShowLoadingIndicator(true);
                }, 300);
                
                setSelectedTrainer('prefix');
                await new Promise(resolve => setTimeout(resolve, 50));
                
                setIsContentReady(true);
                await new Promise(resolve => {
                  requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                      setTimeout(resolve, 50);
                    });
                  });
                });
                
                clearTimeout(loadingTimer);
                setShowLoadingIndicator(false);
                setIsFadingOut(false);
              }}
            >
              ПРЕ/ПРИ
            </Chapter>
            
            <Chapter 
              subject={false}
              func={async () => {
                setIsFadingOut(true);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                setIsContentReady(false);
                
                const loadingTimer = setTimeout(() => {
                  setShowLoadingIndicator(true);
                }, 300);
                
                setSelectedTrainer('dict');
                await new Promise(resolve => setTimeout(resolve, 50));
                
                setIsContentReady(true);
                await new Promise(resolve => {
                  requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                      setTimeout(resolve, 50);
                    });
                  });
                });
                
                clearTimeout(loadingTimer);
                setShowLoadingIndicator(false);
                setIsFadingOut(false);
              }}
            >
              Словарные слова
            </Chapter>
          </div>
          
          <div 
            className="back-to-subjects-button" 
            onClick={() => navigateToPage('subject')}
          />
        </>
      );
    } else {
      let TrainerComponent = null;
      let trainerTitle = '';
      
      if (selectedTrainer === 'stress') {
        TrainerComponent = StressTrainer;
        trainerTitle = 'Орфоэпия (ударения)';
      }
      if (selectedTrainer === 'prefix') {
        TrainerComponent = PrefixTrainer;
        trainerTitle = 'ПРЕ/ПРИ';
      }
      if (selectedTrainer === 'dict') {
        TrainerComponent = DictionaryTrainer;
        trainerTitle = 'Словарные слова';
      }
      
      content = (
        <>
          <Chapter
            isValue="true"
            func={async () => {
              setIsFadingOut(true);
              await new Promise(resolve => setTimeout(resolve, 300));
              
              setIsContentReady(false);
              
              const loadingTimer = setTimeout(() => {
                setShowLoadingIndicator(true);
              }, 300);
              
              setSelectedTrainer(null);
              await new Promise(resolve => setTimeout(resolve, 50));
              
              setIsContentReady(true);
              await new Promise(resolve => {
                requestAnimationFrame(() => {
                  requestAnimationFrame(() => {
                    setTimeout(resolve, 50);
                  });
                });
              });
              
              clearTimeout(loadingTimer);
              setShowLoadingIndicator(false);
              setIsFadingOut(false);
            }}
          >
            {trainerTitle}
          </Chapter>
          
          {TrainerComponent && <TrainerComponent />}
        </>
      );
    }
  } 
  
  if (page === "theory") {
    // 🆕 Передаём предзагруженные данные
    const cachedData = object ? theoryCache[object.id] : null;
    
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => navigateToPage("subject")}
        >
          Теория
        </Chapter>
        <TheoryChoose 
          object={object} 
          preloadedRules={cachedData?.rules}
          preloadedTasks={cachedData?.tasks}
        />
      </>
    )
  }
  
  if (page === "analysis") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => navigateToPage("subject")}
        >
          Аналитика
        </Chapter>
      </>
    )
  }

  return (
    <>
      <div className={`main ${isFadingOut ? 'main--fading-out' : ''}`}>
        {isContentReady ? content : null}
      </div>
      
      {/* Индикатор загрузки */}
      {showLoadingIndicator && (
        <div className="loading-indicator">
          <div className="loading-spinner"></div>
          <div className="loading-text">Загрузка...</div>
        </div>
      )}
    </>
  )
}

export default App

