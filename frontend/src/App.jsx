import { useRef, useState, useEffect, use } from 'react'
import './General.css'
import Chapter from './componentrs/Chapter/chapter.jsx'
import { Element, Popup } from './components.jsx'

// const Names = [
//   {
//     name: "Текст"
//   },
//   {
//     name: "Морфемы"
//   },
//   {
//     name: "Части речи"
//   },
//   {
//     name: "Пунктуация"
//   },
// ]

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


function TheoryChoose({ object }) {
  console.log("-----< Полученный предмет >-----", object); //! console.log


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
  const [rules, setRules] = useState(
    []
  ); // * Долэжен быть fetch на получение имен
  useEffect(() => {
    fetch(`/api/theory/all_theory_for_subject/${object.id}`)  //! Должно быть без localhost
      .then(response => response.json())
      .then(data => {
        // console.log(data)
        setRules(data)
    })
  }, []);

  console.log("-----< Правила >-----", rules); //! console.log

  function handleSelect(id, isChoose) {
    // console.log("ВЫБОР ТЕМЫ", id, isChoose) //! console.log
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
      // console.log(`Вывели всю теорию}`);
      setViewRules(rules);
    } else {
      setViewRules([]);
      // console.log(`Вывели теорию по запросу (id) = ${chosenBlock}`);
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
      <div className={isTaskActive ? "theoryChoose__block theoryChoose__block--active" : "theoryChoose__block--hidden"}>
        Задания
      </div>
      <div className={isThemeActive ? "theoryChoose__block theoryChoose__block--active" : "theoryChoose__block--hidden"}>
        {object.types.map((item, index) => {
          return (
            <Option key={index} onSelect={handleSelect} theme_id={item.id}>{item.name}</Option>
          )
        })}
      </div>
      <div className="elementBlock">
        {viewRules.map((item, index) => {
          return (
            <Element key={index} theory_id={item.id} setPopup={setPopup} setContent={setContent}>{item.name}</Element>
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
    setVar("active-color", isDark ? "rgb(255, 200, 100)" : params.header_bg_color);
  }, []);

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
              setPage("subject");
              
              console.log("------< Предмет >------", item.subject)            //! console.log
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
          func={() => {         
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

            const our = day_task.current;
            our.children[2].style = "transform: translateX(50px);";
            our.children[1].style.animation = "chapter-text 0.5s forwards";
            setTimeout(() => {
              our.children[1].classList.add("chapter__text--after");
              our.children[1].style.animation = "";
              our.children[2].classList.toggle("all--disabled");
              our.children[0].classList.toggle("all--disabled");
            }, 480);

            setTimeout(() => {
              setPage("day-task");
            }, 500);
          }}
        >
          Ежедневное задание
        </Chapter>
        <Chapter 
          ref={task} 
          func={() => {         
            title.current.style.animation = "disable 0.5s";
            day_task.current.style.animation = "disable 0.5s";
            theory.current.style.animation = "disable 0.5s";
            analysis.current.style.animation = "disable 0.5s";
            setTimeout(() => {
              title.current.classList.add("all--disabled");
              day_task.current.classList.add("all--disabled");
              theory.current.classList.add("all--disabled");
              analysis.current.classList.add("all--disabled");
            }, 480);

            const our = task.current;
            our.children[2].style = "transform: translateX(50px);";
            our.children[1].style.animation = "chapter-text 0.5s forwards";
            setTimeout(() => {
              our.children[1].classList.add("chapter__text--after");
              our.children[1].style.animation = "";
              our.children[2].classList.toggle("all--disabled");
              our.children[0].classList.toggle("all--disabled");
            }, 480);

            setTimeout(() => {
              setPage("task");
            }, 500);
          }}
        >
          Практика
        </Chapter>
        <Chapter 
          ref={theory} 
          func={() => {         
            title.current.style.animation = "disable 0.5s";
            day_task.current.style.animation = "disable 0.5s";
            task.current.style.animation = "disable 0.5s";
            analysis.current.style.animation = "disable 0.5s";
            setTimeout(() => {
              title.current.classList.add("all--disabled");
              day_task.current.classList.add("all--disabled");
              task.current.classList.add("all--disabled");
              analysis.current.classList.add("all--disabled");
            }, 480);

            const our = theory.current;
            our.children[2].style = "transform: translateX(50px);";
            our.children[1].style.animation = "chapter-text 0.5s forwards";
            setTimeout(() => {
              our.children[1].classList.add("chapter__text--after");
              our.children[1].style.animation = "";
              our.children[2].classList.toggle("all--disabled");
              our.children[0].classList.toggle("all--disabled");
            }, 480);

            setTimeout(() => {
              setPage("theory");
            }, 500);
          }}
        >
          Теория
        </Chapter>
        <Chapter 
          ref={analysis} 
          func={() => {         
            title.current.style.animation = "disable 0.5s";
            day_task.current.style.animation = "disable 0.5s";
            task.current.style.animation = "disable 0.5s";
            theory.current.style.animation = "disable 0.5s";
            setTimeout(() => {
              title.current.classList.add("all--disabled");
              day_task.current.classList.add("all--disabled");
              task.current.classList.add("all--disabled");
              theory.current.classList.add("all--disabled");
            }, 480);

            const our = analysis.current;
            our.children[2].style = "transform: translateX(50px);";
            our.children[1].style.animation = "chapter-text 0.5s forwards";
            setTimeout(() => {
              our.children[1].classList.add("chapter__text--after");
              our.children[1].style.animation = "";
              our.children[2].classList.toggle("all--disabled");
              our.children[0].classList.toggle("all--disabled");
            }, 480);

            setTimeout(() => {
              setPage("analysis");
            }, 500);
          }}
        >
          Аналитика
        </Chapter>
        <div 
          className="back-to-subjects-button" 
          onClick={() => setPage("main")}
        />
      </>
  }
  if (page === "day-task") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => setPage("subject")}
        >
          Ежедневное задание
        </Chapter>
      </>
    )
  }
  if (page === "task") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => setPage("subject")}
        >
          Практика
        </Chapter>
      </>
    )
  }
  if (page === "theory") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => setPage("subject")}
        >
          Теория
        </Chapter>
        <TheoryChoose object={object} />
      </>
    )
  }
  if (page === "analysis") {
    content = (
      <>
        <Chapter
          isValue="true"
          func={() => {setPage("subject")}}
        >
          Аналитика
        </Chapter>
      </>
    )
  }

  return (
    <>
      <div className="main">
        {content}
      </div>
    </>
  )
}

export default App