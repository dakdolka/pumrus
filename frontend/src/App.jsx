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
    setVar("main-color", params.bg_color);
    setVar("text-color", params.text_color);
    setVar("block-color", params.secondary_bg_color);
    // setVar("secondary-color", params.secondary_bg_color);
  }, []);

  return (
    <>
      <div className="main">
        <Chapter>Теория</Chapter>
        {/* <Chapter>Задания</Chapter> */}
        <TheoryChoose />
      </div>
    </>
  )
}

export default App