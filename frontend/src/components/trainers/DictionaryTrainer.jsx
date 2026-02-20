import React, { useEffect, useRef } from 'react';
import './trainers.css';
import { dictionaryWords } from './data/dictionaryWords.js';
import { useLetterTrainer } from './hooks/useLetterTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

const STORAGE_KEY = 'dictionary_trainer_state_v4';

// заглавная буква = проверяемая, строчная = показываем как есть
function parseWord(word) {
  const chars = [...word];
  const check = [];
  chars.forEach((ch, i) => {
    if (ch.match(/[А-ЯЁ]/)) check.push(i);
  });
  return { original: word, lower: word.toLowerCase(), check };
}

export function DictionaryTrainer({ onExit, exitRef }) {
  const inputRef = useRef(null);
  const activeRef = useRef(null);

  const {
    words, letterStates, stats,
    currentWord, setCurrentWord,
    currentLetter, setCurrentLetter,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    isExiting, setIsExiting,
    showConfirmReset, setShowConfirmReset,
    reset, resetPage, focusFirstEmpty, updateLetterState,
    collectPageMistakes, collectAllMistakes,
    triggerExit,
    currentPage, setCurrentPage, totalPages, start, end,
  } = useLetterTrainer({
    storageKey: STORAGE_KEY,
    rawData: dictionaryWords,
    parseWord,
    onExit,
  });

  useEffect(() => {
    if (exitRef) exitRef.current = triggerExit;
    return () => { if (exitRef) exitRef.current = null; };
  }, [exitRef, triggerExit]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [currentWord, currentLetter, currentPage]);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [currentWord]);

  function handleInput(e) {
    const raw = e.target.value;
    if (!raw) return;

    // берём последний введённый символ
    const letter = raw[raw.length - 1];
    e.target.value = '';

    handleChoice(letter);
  }

  function handleChoice(letter) {
    if (currentWord >= words.length) return;
    const word    = words[currentWord];
    const letters = letterStates[currentWord];
    if (!letters || currentLetter >= letters.length || letters[currentLetter].done) {
      focusFirstEmpty();
      return;
    }

    const charIndex   = word.check[currentLetter];
    const correctChar = word.lower[charIndex];
    const isCorrect   = letter.toLowerCase() === correctChar.toLowerCase();

    const newStates = updateLetterState(
      currentWord, currentLetter,
      { done: true, correct: isCorrect, input: letter.toLowerCase() },
      isCorrect
    );

    // переходим к следующей незаполненной букве
    const nextLetter = currentLetter + 1;
    if (nextLetter < letters.length) {
      setCurrentLetter(nextLetter);
      return;
    }
    // следующее незаполненное слово
    for (let w = currentWord + 1; w < end; w++) {
      if (newStates[w]?.some(ls => !ls.done)) {
        setCurrentWord(w);
        setCurrentLetter(0);
        return;
      }
    }
    for (let w = start; w < currentWord; w++) {
      if (newStates[w]?.some(ls => !ls.done)) {
        setCurrentWord(w);
        setCurrentLetter(0);
        return;
      }
    }
  }

  function renderMistake(chars) {
    return chars.map((item, j) => (
      <span key={j} style={{ color: item.highlight ? 'green' : 'inherit' }}>
        {item.char}
      </span>
    ));
  }

  const pageNav = (
    <PageNav
      currentPage={currentPage}
      totalPages={totalPages}
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

      {/* скрытый инпут для ввода с клавиатуры */}
      <input
        ref={inputRef}
        className="trainer-hidden-input"
        onInput={handleInput}
        readOnly={false}
      />

      <main className="trainer-words">
        {words.slice(start, end).map((word, relIndex) => {
          const absIndex = start + relIndex;
          return (
            <WordInput
              key={absIndex}
              word={word}
              letterStates={letterStates[absIndex] || []}
              isActive={currentWord === absIndex}
              innerRef={currentWord === absIndex ? activeRef : null}
              onClick={() => {
                if (letterStates[absIndex]?.some(ls => !ls.done)) {
                  setCurrentWord(absIndex);
                  setCurrentLetter(
                    letterStates[absIndex].findIndex(ls => !ls.done)
                  );
                  setTimeout(() => inputRef.current?.focus(), 0);
                }
              }}
            />
          );
        })}
      </main>

      {pageNav}

      {showPageMistakes && (
        <MistakesPopup
          title={`Страница ${currentPage + 1} завершена`}
          mistakes={collectPageMistakes()}
          renderMistake={renderMistake}
          stats={stats}
          statsLabel="букв"
          onClose={() => {
            setShowPageMistakes(false);
            if (currentPage < totalPages - 1) setCurrentPage(p => p + 1);
          }}
        />
      )}

      {showAllMistakes && (
        <MistakesPopup
          title="Все ошибки"
          mistakes={collectAllMistakes()}
          renderMistake={renderMistake}
          stats={stats}
          statsLabel="букв"
          onClose={() => setShowAllMistakes(false)}
        />
      )}

      {showExitMistakes && (
        <MistakesPopup
          title="Все ошибки"
          mistakes={collectAllMistakes()}
          renderMistake={renderMistake}
          stats={stats}
          statsLabel="букв"
          isExit={isExiting}
          onClose={() => {
            setShowExitMistakes(false);
            if (isExiting) {
              setIsExiting(false);
              onExit?.();
            }
          }}
        />
      )}

      {showConfirmReset && (
        <ConfirmPopup
          message="Начать весь тренажёр сначала?"
          onConfirm={() => { setShowConfirmReset(false); reset(); }}
          onCancel={() => setShowConfirmReset(false)}
        />
      )}
    </div>
  );
}

function WordInput({ word, letterStates, isActive, innerRef, onClick }) {
  const chars = [...word.lower];
  return (
    <div
      ref={innerRef}
      className={`trainer-word-input${isActive ? ' trainer-word-input--active' : ''}`}
      onClick={onClick}
    >
      {chars.map((ch, charIndex) => {
        const checkIdx = word.check.indexOf(charIndex);

        // обычная буква — просто показываем
        if (checkIdx === -1) {
          return <span key={charIndex} className="trainer-char">{ch}</span>;
        }

        // проверяемая буква
        const ls = letterStates[checkIdx];
        let cls  = 'trainer-letter';
        let display = '';
        if (ls?.done) {
          cls += ls.correct ? ' trainer-letter--correct' : ' trainer-letter--wrong';
          display = ls.input;
        }
        return (
          <span key={charIndex} className={cls}>
            {ls?.done && !ls.correct && (
              <span className="trainer-letter-correct-above">{ch}</span>
            )}
            {display}
          </span>
        );
      })}
    </div>
  );
}
