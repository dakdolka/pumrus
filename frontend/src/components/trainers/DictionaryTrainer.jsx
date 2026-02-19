import React, { useState, useEffect, useRef } from 'react';
import './trainers.css';
import { dictionaryWords } from './data/dictionaryWords.js';
import { useWordTrainer } from './hooks/useWordTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

const STORAGE_KEY = 'dictionary_trainer_state_v3';

function normalize(str) {
  return str.trim().toLowerCase().replace(/ё/g, 'е');
}

export function DictionaryTrainer({ onExit, exitRef }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef(null);

  const {
    words, wordResults, stats,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    isExiting, setIsExiting,
    showConfirmReset, setShowConfirmReset,
    reset, resetPage, updateResult,
    collectPageMistakes, collectAllMistakes,
    triggerExit,
    currentPage, setCurrentPage, totalPages, start, end,
  } = useWordTrainer({
    storageKey: STORAGE_KEY,
    rawData: dictionaryWords,
    createEmptyResult: () => ({ result: 'none', value: '' }),
    onExit,
  });

  // даём App доступ к triggerExit для кнопки в шапке
  useEffect(() => {
    if (exitRef) exitRef.current = triggerExit;
    return () => { if (exitRef) exitRef.current = null; };
  }, [exitRef, triggerExit]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeIndex, currentPage]);

  useEffect(() => {
    const first = wordResults.findIndex((r, i) => i >= start && i < end && r?.result === 'none');
    setActiveIndex(first !== -1 ? first : start);
  }, [currentPage]);

  function handleChange(e) {
    const value = e.target.value;
    const word  = words[activeIndex];
    if (!word) return;

    const isCorrect = normalize(value) === normalize(word.answer);
    const newResult = {
      result: isCorrect ? 'correct' : 'none',
      value,
    };

    updateResult(activeIndex, newResult, isCorrect);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      const word  = words[activeIndex];
      const state = wordResults[activeIndex];
      if (!word || !state) return;

      const isCorrect = normalize(state.value) === normalize(word.answer);
      const finalResult = {
        result: isCorrect ? 'correct' : 'wrong',
        value: state.value,
      };
      const updated = updateResult(activeIndex, finalResult, isCorrect);

      let next = updated.findIndex((r, i) => i > activeIndex && i < end && r.result === 'none');
      if (next === -1) next = updated.findIndex((r, i) => i >= start && i < end && r.result === 'none');
      if (next !== -1) setActiveIndex(next);
    }
  }

  function renderMistake({ word }) {
    return (
      <>
        <span>{word.question}</span>
        {' — '}
        <span style={{ color: 'green' }}>{word.answer}</span>
      </>
    );
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

      <main className="trainer-words">
        <input
          ref={inputRef}
          className="trainer-hidden-input"
          value={wordResults[activeIndex]?.value ?? ''}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
        />
        {words.slice(start, end).map((entry, relIndex) => {
          const absIndex = start + relIndex;
          const state    = wordResults[absIndex];
          const done     = state?.result !== 'none';
          let cls        = 'trainer-word-input';
          if (absIndex === activeIndex && !done) cls += ' trainer-word-input--active';
          if (done && state.result === 'correct') cls += ' trainer-word-input--correct';
          if (done && state.result === 'wrong')   cls += ' trainer-word-input--wrong';

          return (
            <div
              key={absIndex}
              className={cls}
              onClick={() => {
                if (state?.result === 'none') {
                  setActiveIndex(absIndex);
                  setTimeout(() => inputRef.current?.focus(), 0);
                }
              }}
            >
              <span className="trainer-char">{entry.question}</span>
            </div>
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
          statsLabel="слов"
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
          statsLabel="слов"
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
