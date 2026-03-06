import React, { useState, useEffect, useRef } from 'react';
import './trainers.css';
import { useWordTrainer } from './hooks/useWordTrainer.js';
import { TrainerControls, PageNav, MistakesPopup, ConfirmPopup } from './TrainerShared.jsx';

function parseParts(str) {
  const parts = [];
  const regex = /\(([^)]+)\)/g;
  let lastIndex = 0, match;
  while ((match = regex.exec(str)) !== null) {
    if (match.index > lastIndex) parts.push({ type: 'text', value: str.slice(lastIndex, match.index) });
    parts.push({ type: 'marker', value: match[1] });
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < str.length) parts.push({ type: 'text', value: str.slice(lastIndex) });
  return parts;
}

function resolveWord(str, correct) {
  return parseParts(str).map(p => p.value).join(correct === 'separate' ? ' ' : '');
}

export function SpellingTrainer({ onExit, exitRef, rawData, storageKey }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeRef = useRef(null);

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
    createEmptyResult: () => ({ result: 'none', chosen: null }),
    onExit,
  });

  useEffect(() => {
    if (exitRef) exitRef.current = triggerExit;
    return () => { if (exitRef) exitRef.current = null; };
  }, [exitRef, triggerExit]);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [activeIndex]);

  useEffect(() => {
    const first = wordResults.findIndex((r, i) => i >= start && i < end && r?.result === 'none');
    setActiveIndex(first !== -1 ? first : start);
  }, [currentPage]);

  function handleChoose(option) {
    if (wordResults[activeIndex]?.result !== 'none') return;
    const { correct } = words[activeIndex];
    const isCorrect = option === correct;
    const newResult = { result: isCorrect ? 'correct' : 'wrong', chosen: option };
    const updated = updateResult(activeIndex, newResult, isCorrect);
    let next = updated.findIndex((r, i) => i > activeIndex && i < end && r.result === 'none');
    if (next === -1) next = updated.findIndex((r, i) => i >= start && i < end && r.result === 'none');
    if (next !== -1) setActiveIndex(next);
  }

  const renderMistake = ({ word: entry }) => resolveWord(entry.word, entry.correct);
  const isCurrentDone = wordResults[activeIndex]?.result !== 'none';

  const pageNav = (
    <PageNav currentPage={currentPage} totalPages={totalPages}
      onPrev={() => setCurrentPage(p => p - 1)}
      onNext={() => setCurrentPage(p => p + 1)}
    />
  );

  return (
    <div className="trainer-container spelling-trainer-container">
      <TrainerControls
        onResetAll={() => setShowConfirmReset(true)}
        onResetPage={resetPage}
        onMistakes={() => setShowAllMistakes(true)}
      />
      {pageNav}

      <main className="trainer-words">
        {words.slice(start, end).map((entry, relIndex) => {
          const absIndex = start + relIndex;
          return (
            <SpellingItem
              key={absIndex}
              ref={absIndex === activeIndex ? activeRef : null}
              entry={entry}
              result={wordResults[absIndex]}
              isActive={absIndex === activeIndex}
              onClick={() => { if (wordResults[absIndex]?.result === 'none') setActiveIndex(absIndex); }}
            />
          );
        })}
      </main>

      {pageNav}

      <div className="spelling-keyboard">
        <button
          className={`spelling-key${isCurrentDone ? ' spelling-key--disabled' : ''}`}
          disabled={isCurrentDone}
          onClick={() => handleChoose('solid')}
        >Слитно</button>
        <button
          className={`spelling-key${isCurrentDone ? ' spelling-key--disabled' : ''}`}
          disabled={isCurrentDone}
          onClick={() => handleChoose('separate')}
        >Раздельно</button>
      </div>

      {showPageMistakes && (
        <MistakesPopup title={`Страница ${currentPage + 1} завершена`}
          mistakes={collectPageMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="слов"
          onClose={() => { setShowPageMistakes(false); if (currentPage < totalPages - 1) setCurrentPage(p => p + 1); }}
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
          mistakes={collectAllMistakes()} renderMistake={renderMistake}
          stats={stats} statsLabel="слов"
          isExit={isExiting}
          onClose={() => {
            setShowExitMistakes(false);
            if (isExiting) { setIsExiting(false); onExit?.(); }
          }}
        />
      )}
      {showConfirmReset && (
        <ConfirmPopup message="Начать задание сначала?"
          onConfirm={() => { setShowConfirmReset(false); reset(); }}
          onCancel={() => setShowConfirmReset(false)}
        />
      )}
    </div>
  );
}

const SpellingItem = React.forwardRef(function SpellingItem({ entry, result, isActive, onClick }, ref) {
  const { word, correct } = entry;
  const parts = parseParts(word);
  const done  = result?.result !== 'none';
  let cls = 'spelling-item';
  if (isActive && !done) cls += ' spelling-item--active';
  if (done) cls += result.result === 'correct' ? ' spelling-item--correct' : ' spelling-item--wrong';
  return (
    <div ref={ref} className={cls} onClick={onClick}>
      <span className="spelling-word-text">
        {done
          ? resolveWord(word, correct)
          : parts.map((part, i) =>
              part.type === 'marker'
                ? <span key={i} className="spelling-gap">({part.value})</span>
                : <span key={i}>{part.value}</span>
            )
        }
      </span>
    </div>
  );
});
