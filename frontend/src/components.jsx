import './components.css'
import { useState } from 'react'

function Element({ theory_id, children, setPopup, setContent }) {
    var content = {};
    async function getTheory() {
        await fetch(`/api/theory/get_theory/${theory_id}`) //! Должно быть без localhost
        .then(response => response.json())
        .then(data => {
            content.title = data.name
            content.blocks = data.blocks
        })
        
        await setContent(content)
        setPopup(true)
    }

    return (
        <div 
            className="element" 
            onClick={() => {
                getTheory()
            }}
        >
            {children}
        </div>
    )
}


function TaskElement( {is_single, content, children, setPopup, setContent} ) {
    console.log("-----< Задания >-----", content); //! console.log
    const [isTaskBlockOpen, openTaskBlock] = useState(false);

    if (is_single) {
        return (
            <div className="task-theory-block">
                <div className="element">
                    <div 
                        className={isTaskBlockOpen ? "element__name--open" : "element__name--close"}
                        onClick={() => openTaskBlock(prev => {
                            return !prev
                        })}
                    >
                        {children}
                    </div>
                </div>
                <div className={isTaskBlockOpen ? "task-theory-block__content" : "all--disabled"}>
                    {
                        content[0].theories.map((item) => {
                            return (
                                <Element 
                                    key={item.theory_id}
                                    theory_id={item.theory_id}
                                    setPopup={setPopup}
                                    setContent={setContent}
                                >
                                    {item.theory_name}
                                </Element>
                            )
                        })
                    }
                </div>
            </div>
        )
    } else {
        return (
            <div className="task-theory-block">
                <div className="element">
                    <div 
                        className={isTaskBlockOpen ? "element__name--open" : "element__name--close"}
                        onClick={() => openTaskBlock(prev => {
                            return !prev
                        })}
                    >
                        {children}
                    </div>
                </div>
                <div className={isTaskBlockOpen ? "task-theory-block__content" : "all--disabled"}>
                    {
                        content.map((item) => {
                            const [isTaskOpen, openTask] = useState(false);
                            
                            return (
                                <div className="task-element-block" key={item.task_id}>
                                    <div className="element">
                                        <div
                                            className={isTaskOpen ? "element__name--open" : "element__name--close"}
                                            onClick={() => openTask(prev => {
                                                return !prev
                                            })}
                                        >
                                            {item.task_name}
                                        </div>
                                    </div>
                                    <div className={isTaskOpen ? "task-element-block__content" : "all--disabled"}>
                                        {
                                            item.theories.map((item) => {
                                                return (
                                                    <Element 
                                                        key={item.theory_id}
                                                        theory_id={item.theory_id}
                                                        setPopup={setPopup}
                                                        setContent={setContent}
                                                    >
                                                        {item.theory_name}
                                                    </Element>
                                                )
                                            })
                                        }
                                    </div>
                                </div>
                            )
                        })
                    }
                </div>
            </div>
        )
    }
}


function TheoryElem({ item }) {
    function parseBold(text) {
        const parts = text.split(/(\*\*.*?\*\*)/g); 

        return parts.map((part, i) => {
            if (part.startsWith("**") && part.endsWith("**")) {
                return <b key={i}>{part.slice(2, -2)}</b>;
            } if (part.startsWith("*") && part.endsWith("*")) {
                return <i key={i}>{part.slice(1, -1)}</i>;
            }
            return <span key={i}>{part}</span>;
        });
    }


    if (item.type === "group") {
        const [isOpenGroup, openGroup] = useState(false);

        return (
            <div className="theory--group">
                <div 
                    className={isOpenGroup ? "theory--group__header group--open" : "theory--group__header group--close"}
                    onClick={() => openGroup(!isOpenGroup)}
                >
                    {item.content}
                </div>

                <div className={isOpenGroup ? "theory--children" : "all--disabled"}>
                    {item.children.map((child, index) => (
                        <TheoryElem item={child} key={index} />
                    ))}
                </div>
            </div>
        );
    }

    const Content = parseBold(item.content);

    switch (item.type) {
        case "text":
            return <pre className="theory--visual theory__text">{Content}</pre>;

        case "rule":
            return <pre className="theory--visual theory__rule">{Content}</pre>;

        case "subtitle":
            return <pre className="theory--visual theory__subtitle">{Content}</pre>;

        case "example":
            return (
                <div className="example__block">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Пример</legend>
                        <pre className="theory--visual">{Content}</pre>
                    </fieldset>
                </div>
            );

        case "important":
            return (
                <div className="example__block important">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Важно</legend>
                        <pre className="theory--visual">{Content}</pre>
                    </fieldset>
                </div>
            );

        case "exception":
            return (
                <div className="example__block exception">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Исключение</legend>
                        <pre className="theory--visual">{Content}</pre>
                    </fieldset>
                </div>
            );
    }
}


function Popup({ isPopup, setPopup, content }) {
    // console.log("------< Объект в попапе >------", content) // ! console.log

    return (
        <div className={isPopup ? "popup" : "popup all--disabled"}>
            <div className="popup__header">
                <div className="popup__button" onClick={() => setPopup(false)}></div>
                <div className="popup__title">{content?.title}</div>
            </div>
            <div className="popup__content">
                {
                    content?.blocks.map((item, index) =>  <TheoryElem item={item} key={index} />)
                }   
            </div>
        </div>
    )
}


export { Element, TaskElement, Popup }