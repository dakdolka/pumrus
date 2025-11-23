import './components.css'

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


function Popup({ isPopup, setPopup, content }) {
    // ! console.log
    console.log("------< Объект в попапе >------", content)

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


    function getElem(item, index) {
        if (item.type === 'group') {
            console.log("------< Имя группы >------", item) //!

            item.children.map((item, index) => {
                getElem(item, index)
            })
        } else {
            console.log("------< Элемент >------", item) //!

            const Content = parseBold(item.content)
            if (item.type === 'text') {
                return (
                    <div key={index} className="theory--visual theory__text">{Content}</div>
                )
            } if (item.type === 'subtitle') {
                return (
                    <div key={index} className="theory--visual theory__subtitle">{Content}</div>
                )
            } if (item.type === 'example') {
                return (
                    <div key={index} className="example__block">
                        <fieldset className="theory__example--fieldset">
                            <legend className="theory__example--legend">Пример</legend>
                            <div key={index} className="theory--visual">{Content}</div>
                        </fieldset>
                    </div>
                )
            } if (item.type === 'important') {
                return (
                    <div key={index} className="example__block important">
                        <fieldset className="theory__example--fieldset">
                            <legend className="theory__example--legend">Важно</legend>
                            <div key={index} className="theory--visual">{Content}</div>
                        </fieldset>
                    </div>
                )
            } if (item.type === 'exception') {
                return (
                    <div key={index} className="example__block exception">
                        <fieldset className="theory__example--fieldset">
                            <legend className="theory__example--legend">Исключение</legend>
                            <div key={index} className="theory--visual">{Content}</div>
                        </fieldset>
                    </div>
                )
            }
        }
    }

    return (
        <div className={isPopup ? "popup" : "popup all--disabled"}>
            <div className="popup__header">
                <div className="popup__button" onClick={() => setPopup(false)}></div>
                <div className="popup__title">{content?.title}</div>
            </div>
            <div className="popup__content">
                {
                    content?.blocks.map((item, index) => getElem(item, index))
                }   
            </div>
        </div>
    )
}


export { Element, Popup }