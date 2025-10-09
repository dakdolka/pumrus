import './chapter.css'

function Chapter({ children }) {
    return (
        <div className="chapter">
            <div className="chapter__text">
                {children}
            </div>
            <div className="chapter__icon" />
        </div>
    )
}

export default Chapter