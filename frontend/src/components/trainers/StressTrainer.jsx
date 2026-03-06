import React, { useEffect } from 'react';
import './trainers.css';
import { useWordTrainer } from './hooks/useWordTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

const vowels = 'аеёиоуыэюя';

export function StressTrainer({ onExit, exitRef, rawData, storageKey }) {
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
    storageKey,
    rawData,
    createEmptyResult: () => ({ result: 'none', clicked: [] }),
    onExit,
  });

  useEffect(() => {
    if (exitRef) exitRef.current = triggerExit;
    return () => { if (exitRef) exitRef.current = null; };
  }, [exitRef, triggerExit]);

  function handleVowelClick(absIndex, charIndex) {
    if (wordResults[absIndex]?.result !== 'none') return;
    const chars = [...words[absIndex].question];
    const correctIndex = chars.findIndex(ch => ch !== ch.toLowerCase());
    if (correctIndex === -1) return;
    const isCorrect = charIndex === correctIndex;
    updateResult(absIndex, {
      result: isCorrect ? 'correct' : 'wrong',
      clicked: [...(wordResults[absIndex].clicked ?? []), charIndex],
      correctIndex,
    }, isCorrect);
  }

  function renderMistake({ word }) {
    return [...word.question].map((ch, j) =>
      ch !== ch.toLowerCase()
        ? <span key={j} style={{ color: 'green' }}>{ch}</span>
        : <span key={j}>{ch.toLowerCase()}</span>
    );
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
            <WordDisplay
              key={absIndex}
              word={word.question}
              result={wordResults[absIndex]}
              onVowelClick={charIndex => handleVowelClick(absIndex, charIndex)}
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
          stats={stats} statsLabel="слов"
          onClose={() => {
            setShowPageMistakes(false);
            if (currentPage < totalPages - 1) setCurrentPage(p => p + 1);
          }}
        />
      )}
      {showAllMistakes && (
        <MistakesPopup title="Все ошибки"
          mistakes={collectAllMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="слов"
          onClose={() => setShowAllMistakes(false)}
        />
      )}
      {showExitMistakes && (
        <MistakesPopup
          title="Все ошибки"
          mistakes={collectAllMistakes()}
          renderMistake={renderMistake}
          stats={stats} statsLabel="слов"
          isExit={isExiting}
          onClose={() => {
            setShowExitMistakes(false);
            if (isExiting) { setIsExiting(false); onExit?.(); }
          }}
        />
      )}
      {showConfirmReset && (
        <ConfirmPopup
          message="Начать задание сначала?"
          onConfirm={() => { setShowConfirmReset(false); reset(); }}
          onCancel={() => setShowConfirmReset(false)}
        />
      )}
    </div>
  );
}

function WordDisplay({ word, result, onVowelClick }) {
  const chars = [...word];
  const correctIndex = chars.findIndex(ch => ch !== ch.toLowerCase());
  return (
    <div className={`trainer-word-display ${result?.result !== 'none' ? 'trainer-word-display--done' : ''}`}>
      {chars.map((ch, charIndex) => {
        const lowerCh = ch.toLowerCase();
        if (!vowels.includes(lowerCh)) return <span key={charIndex} className="trainer-char">{lowerCh}</span>;
        const isCorrect    = charIndex === correctIndex;
        const wasClicked   = result?.clicked?.includes(charIndex);
        const isWrongClick = wasClicked && !isCorrect && result?.result === 'wrong';
        let displayChar = lowerCh;
        let className   = 'trainer-vowel-slot';
        if (result?.result === 'correct' && isCorrect) {
          className += ' trainer-vowel-slot--correct'; displayChar = lowerCh.toUpperCase();
        } else if (result?.result === 'wrong') {
          if (isWrongClick) className += ' trainer-vowel-slot--wrong';
          else if (isCorrect) { className += ' trainer-vowel-slot--correct'; displayChar = lowerCh.toUpperCase(); }
        } else {
          className += ' trainer-vowel-slot--clickable';
        }
        return (
          <span key={charIndex} className={className}
            onClick={() => result?.result === 'none' && onVowelClick(charIndex)}>
            {displayChar}
          </span>
        );
      })}
    </div>
  );
}
