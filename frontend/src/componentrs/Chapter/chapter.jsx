import './chapter.css'

function Chapter({ children, page, setPage }) {
    return (
        <div className="chapter" onClick={() => setPage(page)}>
            <div className="chapter__text">
                {children}
            </div>
            <div className="chapter__icon" />
        </div>
    )
}

export default Chapter