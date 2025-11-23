import './components.css'
import { useState } from 'react'

function Element({ theory_id, children, setPopup, setContent }) {
    var content = {};
    fetch(`http://localhost:8000/api/theory/get_theory/${theory_id}`)
        .then(response => response.json())
        .then(data => {
            content.title = data.name
            content.blocks = data.blocks
        })

    return (
        <div 
            className="element" 
            onClick={() => {
                setContent(content)
                setPopup(true)
            }}
        >
            {children}
        </div>
    )
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
            return <div className="theory--visual theory__text">{Content}</div>;

        case "subtitle":
            return <div className="theory--visual theory__subtitle">{Content}</div>;

        case "example":
            return (
                <div className="example__block">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Пример</legend>
                        <div className="theory--visual">{Content}</div>
                    </fieldset>
                </div>
            );

        case "important":
            return (
                <div className="example__block important">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Важно</legend>
                        <div className="theory--visual">{Content}</div>
                    </fieldset>
                </div>
            );

        case "exception":
            return (
                <div className="example__block exception">
                    <fieldset className="theory__example--fieldset">
                        <legend className="theory__example--legend">Исключение</legend>
                        <div className="theory--visual">{Content}</div>
                    </fieldset>
                </div>
            );
    }
}


function Popup({ isPopup, setPopup, content }) {
    // ! console.log
    // console.log("------< Объект в попапе >------", content)

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


export { Element, Popup }