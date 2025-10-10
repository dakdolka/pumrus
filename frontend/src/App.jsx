import { useRef, useState, useEffect, use } from 'react'
import './General.css'
import Chapter from './componentrs/Chapter/chapter.jsx'

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
    </>
  )
}

function App() {
  const [page, setPage] = useState("main");

  useEffect(() => {
    const tg = window.Telegram.WebApp || {};
    tg.ready?.();
    tg.expand?.();

    const params = tg.themeParams || {};
    const root = document.documentElement;

    // Функция — задаёт переменные, если они есть
    function setVar(name, value) {
      if (value) root.style.setProperty(`--${name}`, value);
    }

    // Передаём основные цвета Telegram темы
    setVar("text-color", params.text_color);
    setVar("main-color", params.bg_color);
    setVar("block-color", params.secondary_bg_color);
  }, []);

  let content;
  if (page === "main") {
    content = 
      <>
        <div className="main">
          <div className="mainTitle">
            <div className="mainTitle__picture" />
            <div className="mainTitle__title">PumRus</div>
            <div className="mainTitle__text">Супер крутой бот для подготовки к ЕГЭ. Йоу да свег супер топ МММ ++</div>
          </div>
          <Chapter page={"day-task"} setPage={setPage}>Ежедневное задание</Chapter>
          <Chapter page={"task"} setPage={setPage}>Практика</Chapter>
          <Chapter page={"theory"} setPage={setPage}>Теория</Chapter>
          <Chapter page={"analysis"} setPage={setPage}>Аналитика</Chapter>
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