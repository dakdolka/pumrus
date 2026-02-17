import React, { forwardRef } from "react";
import './chapter.css'

const Chapter = forwardRef(({ children, func, isValue=false, subject=false }, ref) => {
    if (subject) {
        return (
            <div ref={ref} className="chapter" onClick={() => func()}>
                <div className="chapter__text--subject">
                    {children}
                </div>
            </div>
        )
    } else {
        return (
            <div ref={ref} className="chapter" onClick={() => func()}>
                <div className={isValue ? "chapter__icon chapter__icon--close" : "chapter__icon chapter__icon--close all--disabled"} />
                <div className={isValue ? "chapter__text chapter__text--after" : "chapter__text"}>
                    {children}
                </div>
                <div className={isValue ?  "chapter__icon chapter__icon--open all--disabled": "chapter__icon chapter__icon--open"} />
            </div>
    )
    }
});

export default Chapter