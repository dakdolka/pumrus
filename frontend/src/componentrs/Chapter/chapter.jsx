import React, { forwardRef } from "react";
import './chapter.css'

const Chapter = forwardRef(({ children, func }, ref) => {
    return (
        <div ref={ref} className="chapter" onClick={() => func()}>
            <div className="chapter__icon chapter__icon--close all--disabled" />
            <div className="chapter__text">
                {children}
            </div>
            <div className="chapter__icon chapter__icon--open" />
        </div>
    )
});

export default Chapter