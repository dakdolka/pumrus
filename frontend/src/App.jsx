import { useRef, useState, useEffect, use } from 'react'
import './General.css'
import Chapter from './componentrs/Chapter/chapter.jsx'
import { Element } from './components.jsx'

const Names = [
  {
    name: "Текст"
  },
  {
    name: "Морфемы"
  },
  {
    name: "Части речи"
  },
  {
    name: "Пунктуация"
  },
]

function saveInfo(key, value) {
    const jsonString = JSON.stringify(value);
    localStorage.setItem(key, jsonString);
}

function getInfo(key) {
    const jsonString = localStorage.getItem(key);
    return JSON.parse(jsonString);
}


function Option({ children, onSelect }) {
  const [isChosen, setMood] = useState(false);

  return (
    <div className="option" data-ischosen={isChosen.toString()} onClick={() => {
        setMood(prev => {
          onSelect(children, !prev);
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


function TheoryChoose() {
  const task = useRef();
  const theme = useRef();

  const [isTaskActive, setTaskMood] = useState(false);
  const [isThemeActive, setThemeMood] = useState(false);

  const [chosenBlock, setChosenBlock] = useState([]);

  const [rules, setRules] = useState(
    []
  ); // * Долэжен быть fetch на получение имен
  fetch("/api/theory/all_theory")
    .then(response => response.json())
    .then(data => {
      console.log(data)
      // setRules(data)
  })

  function handleSelect(name, isChoose) {
    setChosenBlock(prev => {
      if (isChoose) {
        if (!prev.includes(name)) return [...prev, name];
        return prev;
      } else {
        return prev.filter(item => item !== name);
      }
    });
  };

  useEffect(() => {
    // console.log(`Вывели теорию по запросу = ${chosenBlock}`);
  }, [chosenBlock]);

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
      <div className={isTaskActive ? "theoryChoose__block theoryChoose__block--active" : "theoryChoose__block--hidden"}>
        Задания
      </div>
      <div className={isThemeActive ? "theoryChoose__block theoryChoose__block--active" : "theoryChoose__block--hidden"}>
        {Names.map((item, index) => {
          return (
            <Option key={index} onSelect={handleSelect}>{item.name}</Option>
          )
        })}
      </div>
      <div className="elementBlock">
        {rules.map((item, index) => {
          return (
            <Element key={index}>{item}</Element>
          )
        })}
      </div>
    </>
  )
}

function App() {
  const day_task = useRef();
  const task = useRef();
  const theory = useRef();
  const analysis = useRef();
  const title = useRef();

  const [page, setPage] = useState("main");

  useEffect(() => {
    const tg = window.Telegram.WebApp || {};
    tg.ready?.();
    tg.expand?.();

    const params = tg.themeParams || {};
    const isDark = tg.colorScheme === "dark";
    const root = document.documentElement;

    // Функция — задаёт переменные, если они есть
    function setVar(name, value) {
      if (value) root.style.setProperty(`--${name}`, value);
    }

    // Передаём основные цвета Telegram темы
    setVar("text-color", params.text_color);
    setVar("text-color", params.text_color);
    setVar("main-color", params.bg_color);
    setVar("block-color", isDark ? params.section_bg_color : params.secondary_bg_color);
    setVar("active-color", isDark ? "rgb(85, 85, 255)" : params.header_bg_color);
  }, []);

  let content;
  if (page === "main") {
    content = 
      <>
        <div className="main">
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
            func={() => {
              // console.log(title.current.style);           
              title.current.style.animation = "disable 0.5s";
              task.current.style.animation = "disable 0.5s";
              theory.current.style.animation = "disable 0.5s";
              analysis.current.style.animation = "disable 0.5s";
              setTimeout(() => {
                title.current.classList.add("all--disabled");
                task.current.classList.add("all--disabled");
                theory.current.classList.add("all--disabled");
                analysis.current.classList.add("all--disabled");
              }, 480);

              day_task.current.children[2].style = "transform: translateX(50px);";
              day_task.current.children[1].style.animation = "chapter-text 0.5s";
              setTimeout(() => {
                day_task.current.children[1].classList.add("chapter__text--after");
                day_task.current.children[2].classList.toggle("all--disabled");
                day_task.current.children[0].classList.toggle("all--disabled");
              }, 480);
            }}
          >
            Ежедневное задание
          </Chapter>
          <Chapter 
            ref={task} 
            funs={() => {

            }}
          >
            Практика
          </Chapter>
          <Chapter 
            ref={theory} 
            funs={() => {

            }}
          >
            Теория
          </Chapter>
          <Chapter 
            ref={analysis} 
            funs={() => {

            }}
          >
            Аналитика
          </Chapter>
        </div>
      </>
  }
  if (page === "day-task") {
    content = (
      <>
        Кто прочитал тот лох
      </>
    )
  }
  if (page === "task") {
    content = (
      <>
        Кто прочитал тот лох
      </>
    )
  }
  if (page === "theory") {
    content = (
      <>
        <div className="main">
          <Chapter page={"main"} setPage={setPage}>назад</Chapter>
          <TheoryChoose />
        </div>
      </>
    )
  }
  if (page === "analysis") {
    content = (
      <>
        Кто прочитал тот лох
      </>
    )
  }

  return (
    <>
      {content}
    </>
  )
}

export default App