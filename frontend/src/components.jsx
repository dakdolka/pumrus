import './components.css'
import { useState } from 'react'
import React from 'react'


function Element({ theory_id, children, setPopup, setContent }) {
    const [isLoading, setIsLoading] = useState(false);

    async function getTheory() {
        setIsLoading(true);
        var content = {};
        await fetch(`/api/theory/get_theory/${theory_id}`)
            .then(response => response.json())
            .then(data => {
                content.title = data.name;
                content.blocks = data.blocks;
            });
        await new Promise(resolve => setTimeout(resolve, 100));
        await setContent(content);
        setPopup(true);
        setIsLoading(false);
    }

    return (
        <div
            className={`element${isLoading ? ' element--loading' : ''}`}
            onClick={getTheory}
        >
            <span className="element__title">{children}</span>
        </div>
    )
}


function TaskElement({ is_single, content, children, setPopup, setContent }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="task-theory-block">
            <div
                className={`element element--toggle${isOpen ? ' element--opened' : ''}`}
                onClick={() => setIsOpen(prev => !prev)}
            >
                <span className={`element__arrow${isOpen ? ' element__arrow--open' : ''}`} />
                <span className="element__title">{children}</span>
            </div>

            <div className={isOpen ? "task-theory-block__content" : "all--disabled"}>
                {is_single
                    ? content[0].theories.map((item) => (
                        <Element
                            key={item.theory_id}
                            theory_id={item.theory_id}
                            setPopup={setPopup}
                            setContent={setContent}
                        >
                            {item.theory_name}
                        </Element>
                    ))
                    : content.map((item, i) => (
                        <TaskSubElement
                            key={i}
                            item={item}
                            setPopup={setPopup}
                            setContent={setContent}
                        />
                    ))
                }
            </div>
        </div>
    )
}


function TaskSubElement({ item, setPopup, setContent }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="task-element-block">
            <div
                className={`element element--toggle${isOpen ? ' element--opened' : ''}`}
                onClick={() => setIsOpen(prev => !prev)}
            >
                <span className={`element__arrow${isOpen ? ' element__arrow--open' : ''}`} />
                <span className="element__title">{item.task_name}</span>
            </div>

            <div className={isOpen ? "task-element-block__content" : "all--disabled"}>
                {item.theories.map((theory) => (
                    <Element
                        key={theory.theory_id}
                        theory_id={theory.theory_id}
                        setPopup={setPopup}
                        setContent={setContent}
                    >
                        {theory.theory_name}
                    </Element>
                ))}
            </div>
        </div>
    )
}


function TheoryElem({ item, groupPath = '' }) {
    function parseBold(text) {
        const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
        return parts.flatMap((part, i) => {
            if (part.startsWith("**") && part.endsWith("**"))
                return <b key={i}>{part.slice(2, -2)}</b>;
            if (part.startsWith("*") && part.endsWith("*"))
                return <i key={i}>{part.slice(1, -1)}</i>;
            return part.split("\\n").map((line, j, arr) => (
                <React.Fragment key={`${i}-${j}`}>
                    {line}
                    {j < arr.length - 1 && <br />}
                </React.Fragment>
            ));
        });
    }

    if (item.type === "group") {
        const [isOpen, setIsOpen] = useState(false);
        const sortedChildren = [...(item.children || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

        return (
            <div className="theory--group">
                <div
                    className={`theory--group__header${isOpen ? ' group--open' : ' group--close'}`}
                    onClick={() => setIsOpen(prev => !prev)}
                >
                    <span className={`element__arrow${isOpen ? ' element__arrow--open' : ''}`} />
                    <span>{item.content}</span>
                </div>
                <div className={isOpen ? "theory--children" : "all--disabled"}>
                    {sortedChildren.map((child, index) => (
                        <TheoryElem item={child} key={index} groupPath={groupPath} />
                    ))}
                </div>
            </div>
        );
    }

    const Content = parseBold(item.content);

    switch (item.type) {
        case "text":
            return <div className="theory--visual theory__text">{Content}</div>;

        case "link":
            return <a href={item.content} className="theory__link">тренажер <span className="theory__link-arrow">↗</span></a>;

        case "rule":
            return (
                <div className="example__block">
                    <fieldset className="theory__example--fieldset theory__example--fieldset--rule">
                        <legend className="theory__example--legend theory__example--legend--rule">
                            Правило
                        </legend>
                        <div className="theory--visual theory__rule">
                            {Content}
                        </div>
                    </fieldset>
                </div>
            );
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
                <div className="example__block">
                    <fieldset className="theory__example--fieldset theory__example--fieldset--important">
                        <legend className="theory__example--legend theory__example--legend--important">Важно</legend>
                        <div className="theory--visual">{Content}</div>
                    </fieldset>
                </div>
            );

        case "exception":
            return (
                <div className="example__block">
                    <fieldset className="theory__example--fieldset theory__example--fieldset--exception">
                        <legend className="theory__example--legend theory__example--legend--exception">Исключение</legend>
                        <div className="theory--visual">{Content}</div>
                    </fieldset>
                </div>
            );

        default:
            return null;
    }
}


function Popup({ isPopup, setPopup, content }) {
    const [isContentReady, setIsContentReady] = useState(false);
    const [showContent, setShowContent] = useState(false);

    React.useEffect(() => {
        if (isPopup) {
            setIsContentReady(false);
            setShowContent(false);
            setTimeout(() => {
                setIsContentReady(true);
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        setShowContent(true);
                    });
                });
            }, 100);
        }
    }, [isPopup, content]);

    const sortedBlocks = [...(content?.blocks || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

    return (
        <div className={isPopup ? "popup" : "popup all--disabled"}>
            <div className="popup__header">
                <button className="popup__button" onClick={() => setPopup(false)} aria-label="Закрыть" />
                <div className="popup__title">{content?.title}</div>
            </div>

            {isPopup && !showContent && (
                <div className="popup__loading">
                    <div className="popup__spinner" />
                    <div className="popup__loading-text">Загрузка...</div>
                </div>
            )}

            <div className={`popup__content${showContent ? ' popup__content--visible' : ' popup__content--hidden'}`}>
                {isContentReady && sortedBlocks.map((item, index) => (
                    <TheoryElem item={item} key={index} />
                ))}
            </div>
        </div>
    )
}


export { Element, TaskElement, Popup }
