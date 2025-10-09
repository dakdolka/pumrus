import './General.css'
import Chapter from './componentrs/Chapter/chapter.jsx'

function TheoryChoose({ children }) {
  return (
    <div className="theoryChoose">
      {children}
    </div>
  )
}

function App() {
  return (
    <>
      <div className="main">
        <Chapter>Теория</Chapter>
        {/* <Chapter>Задания</Chapter> */}
        <TheoryChoose>
          <div className="theotyChoose__elem theoryChoose__task"></div>
          <div className="theotyChoose__elem theoryChoose__theme"></div>
        </TheoryChoose>
      </div>
    </>
  )
}

export default App