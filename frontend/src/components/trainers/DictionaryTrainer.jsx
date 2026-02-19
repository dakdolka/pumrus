import React, { useRef, useEffect } from 'react';
import './trainers.css';
import { dictionaryWords } from './data/dictionaryWords.js';
import { useLetterTrainer } from './hooks/useLetterTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

const STORAGE_KEY = 'dict_words_trainer_state_v2';

function parseWord(word) {
  const chars = [...word], check = [];
  chars.forEach((ch, i) => { if (ch === ch.toUpperCase() && ch.match(/[А-ЯЁ]/)) check.push(i); });
  return { original: word, lower: word.toLowerCase(), check };
}

export function DictionaryTrainer({ onExit }) {
  const {
    words, letterStates, stats,
    currentWord, setCurrentWord,
    currentLetter, setCurrentLetter,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showConfirmReset, setShowConfirmReset,
    reset, resetPage, focusFirstEmpty, updateLetterState,
    collectPageMistakes, collectAllMistakes,
    currentPage, setCurrentPage, totalPages, start, end,
  } = useLetterTrainer({
    storageKey: STORAGE_KEY,
    rawData: dictionaryWords,
    parseWord,
    onExit,
  });

  function handleInput(value) {
    if (!value || currentWord >= words.length) return;
    const word    = words[currentWord];
    const letters = letterStates[currentWord];
    if (currentLetter >= letters.length || letters[currentLetter].done) { focusFirstEmpty(); return; }
    const charIndex   = word.check[currentLetter];
    const correctChar = word.lower[charIndex];
    const isCorrect   = value.toLowerCase() === correctChar;
    const newStates = updateLetterState(
      currentWord, currentLetter,
      { done: true, correct: isCorrect, input: value.toLowerCase() },
      isCorrect
    );
    const nextLetter = currentLetter + 1;
    if (nextLetter < letters.length) { setCurrentLetter(nextLetter); return; }
    for (let w = currentWord + 1; w < end; w++) {
      if (newStates[w]?.some(ls => !ls.done)) { setCurrentWord(w); setCurrentLetter(0); return; }
    }
    for (let w = start; w < currentWord; w++) {
      if (newStates[w]?.some(ls => !ls.done)) { setCurrentWord(w); setCurrentLetter(0); return; }
    }
  }

  function renderMistake(chars) {
    return chars.map((item, j) => (
      <span key={j} style={{ color: item.highlight ? 'green' : 'inherit' }}>{item.char}</span>
    ));
  }

  const pageNav = (
    <PageNav currentPage={currentPage} totalPages={totalPages}
      onPrev={() => setCurrentPage(p => p - 1)}
      onNext={() => setCurrentPage(p => p + 1)}
    />
  );

  return (
    <div className="trainer-container">
      <TrainerControls
        onResetAll={() => setShowConfirmReset(true)}
        onResetPage={resetPage}
        onMistakes={() => setShowAllMistakes(true)}
      />
      {pageNav}

      <main className="trainer-words">
        {words.slice(start, end).map((word, relIndex) => {
          const absIndex = start + relIndex;
          return (
            <WordInput
              key={absIndex}
              word={word}
              letterStates={letterStates[absIndex] || []}
              isActive={currentWord === absIndex}
              onInput={handleInput}
            />
          );
        })}
      </main>

      {pageNav}  {/* пункт 3 */}

      {showPageMistakes && (
        <MistakesPopup title={`Страница ${currentPage + 1} завершена`}
          mistakes={collectPageMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="букв"
          onClose={() => { setShowPageMistakes(false); if (currentPage < totalPages - 1) setCurrentPage(p => p + 1); }}
        />
      )}
      {showAllMistakes && (
        <MistakesPopup title="Все ошибки"
          mistakes={collectAllMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="букв"
          onClose={() => setShowAllMistakes(false)}
        />
      )}
      {showExitMistakes && (
        <MistakesPopup title="Все ошибки"
          mistakes={collectAllMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="букв"
          onClose={() => { setShowExitMistakes(false); onExit?.(); }}
        />
      )}
      {showConfirmReset && (
        <ConfirmPopup message="Начать весь тренажёр сначала?"
          onConfirm={() => { setShowConfirmReset(false); reset(); }}
          onCancel={() => setShowConfirmReset(false)}
        />
      )}
    </div>
  );
}

function WordInput({ word, letterStates, isActive, onInput }) {
  const hiddenInputRef = useRef(null);
  const chars = [...word.lower];
  let letterIndex = 0;
  useEffect(() => { if (isActive) hiddenInputRef.current?.focus(); }, [isActive]);
  function handleInput(e) {
    const value = e.target.value;
    if (value && /[а-яёА-ЯЁ]/i.test(value)) onInput(value);
    e.target.value = '';
  }
  return (
    <div className={`trainer-word-input ${isActive ? 'trainer-word-input--active' : ''}`}
      onClick={() => hiddenInputRef.current?.focus()}>
      {chars.map((ch, charIndex) => {
        if (word.check.includes(charIndex)) {
          const state = letterStates[letterIndex];
          const className = `trainer-letter ${state?.done ? (state.correct ? 'trainer-letter--correct' : 'trainer-letter--wrong') : ''}`;
          letterIndex++;
          return (
            <span key={charIndex} className={className}>
              {state?.done && !state.correct && <span className="trainer-letter-correct-above">{ch}</span>}
              {state?.done ? state.input : '\u00A0'}
            </span>
          );
        }
        return <span key={charIndex} className="trainer-char">{ch}</span>;
      })}
      <input ref={hiddenInputRef} type="text" className="trainer-hidden-input"
        autoComplete="off" spellCheck="false" inputMode="text" onInput={handleInput} />
    </div>
  );
}
