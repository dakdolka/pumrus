import React from 'react';
import './trainers.css';
import { stressWords } from './data/stressWords.js';
import { useWordTrainer } from './hooks/useWordTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

const STORAGE_KEY = 'stress_trainer_state_v11';
const vowels = 'аеёиоуыэюя';

export function StressTrainer({ onExit }) {
  const {
    words, wordResults, stats,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showConfirmReset, setShowConfirmReset,
    reset, resetPage, updateResult,
    collectPageMistakes, collectAllMistakes,
    currentPage, setCurrentPage, totalPages, start, end,
  } = useWordTrainer({
    storageKey: STORAGE_KEY,
    rawData: stressWords,
    createEmptyResult: () => ({ result: 'none', clicked: [] }),
    onExit,
  });

  function handleVowelClick(absIndex, charIndex) {
    if (wordResults[absIndex]?.result !== 'none') return;
    const chars = [...words[absIndex]];
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
    return [...word].map((ch, j) =>
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
        onMistakes={() => setShowAllMistakes(true)}  // пункт 4
      />
      {pageNav}

      <main className="trainer-words">
        {words.slice(start, end).map((word, relIndex) => {
          const absIndex = start + relIndex;
          return (
            <WordDisplay
              key={absIndex}
              word={word}
              result={wordResults[absIndex]}
              onVowelClick={charIndex => handleVowelClick(absIndex, charIndex)}
            />
          );
        })}
      </main>

      {pageNav}  {/* пункт 3 — навигация снизу */}

      {/* Автопопап при завершении страницы — показывает ошибки страницы */}
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
      {/* Кнопка "Ошибки" — показывает все ошибки (пункт 4/5) */}
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
      {/* Попап при выходе — показывает все ошибки */}
      {showExitMistakes && (
        <MistakesPopup
          title="Все ошибки"
          mistakes={collectAllMistakes()}
          renderMistake={renderMistake}
          stats={stats}
          statsLabel="слов"
          onClose={() => { setShowExitMistakes(false); onExit?.(); }}
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
