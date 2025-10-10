import './components.css'

function Element({ children }) {
    return (
        <div 
            className="element" 
            onClick={() => {
                console.log(children)
            }}
        >
            {children}
        </div>
    )
}

export { Element }