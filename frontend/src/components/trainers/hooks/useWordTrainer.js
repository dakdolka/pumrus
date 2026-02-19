import { useState, useEffect } from 'react';
import { shuffleArray, loadState, saveState } from '../trainerUtils.js';
import { useTrainerPagination } from './useTrainerPagination.js';

export function useWordTrainer({ storageKey, rawData, createEmptyResult, onExit }) {
  const [words,       setWords]       = useState([]);
  const [wordResults, setWordResults] = useState([]);
  const [stats,       setStats]       = useState({ total: 0, correct: 0, wrong: 0 });
  const [showPageMistakes, setShowPageMistakes] = useState(false);
  const [showAllMistakes,  setShowAllMistakes]  = useState(false); // пункт 4/5
  const [showExitMistakes, setShowExitMistakes] = useState(false);
  const [showConfirmReset, setShowConfirmReset] = useState(false);

  const pagination = useTrainerPagination({
    items: wordResults,
    isPageDone: slice => slice.every(r => r?.result !== 'none'),
    onPageComplete: () => setShowPageMistakes(true),
  });

  const {
    currentPage, setCurrentPage,
    start, end,
    initShownPages, allowPageAgain, resetShownPages,
  } = pagination;

  useEffect(() => {
    const saved = loadState(storageKey);
    if (saved) {
      setWords(saved.words ?? []);
      setWordResults(saved.wordResults ?? []);
      setStats({ total: saved.total ?? 0, correct: saved.correct ?? 0, wrong: saved.wrong ?? 0 });
      setCurrentPage(saved.currentPage ?? 0);
      initShownPages(saved.wordResults ?? []);
    } else {
      _reset();
    }
  }, []);

  useEffect(() => {
    if (words.length > 0) {
      saveState(storageKey, { words, wordResults, ...stats, currentPage });
    }
  }, [words, wordResults, stats, currentPage]);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;
    const handleBack = () => {
      if (currentPage > 0) setCurrentPage(p => p - 1);
      else _triggerExit();
    };
    tg.onEvent('backButtonClicked', handleBack);
    return () => tg.offEvent?.('backButtonClicked', handleBack);
  }, [currentPage, words, wordResults]);

  function _reset() {
    if (!rawData?.length) return;
    const shuffled = shuffleArray([...rawData]);
    setWords(shuffled);
    setWordResults(shuffled.map(() => createEmptyResult()));
    setStats({ total: shuffled.length, correct: 0, wrong: 0 });
    setCurrentPage(0);
    resetShownPages();
    localStorage.removeItem(storageKey);
  }

  function resetPage() {
    let pageCorrect = 0, pageWrong = 0;
    for (let i = start; i < end; i++) {
      if (wordResults[i]?.result === 'correct') pageCorrect++;
      if (wordResults[i]?.result === 'wrong')   pageWrong++;
    }
    const newResults = [...wordResults];
    for (let i = start; i < end; i++) newResults[i] = createEmptyResult();
    setWordResults(newResults);
    setStats(prev => ({ ...prev, correct: prev.correct - pageCorrect, wrong: prev.wrong - pageWrong }));
    allowPageAgain();
  }

  function updateResult(absIndex, newResult, isCorrect) {
    const updated = [...wordResults];
    updated[absIndex] = newResult;
    setWordResults(updated);
    setStats(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      wrong:   prev.wrong   + (isCorrect ? 0 : 1),
    }));
    return updated;
  }

  function collectPageMistakes() {
    return words.slice(start, end)
      .map((word, i) => ({ word, result: wordResults[start + i]?.result }))
      .filter(item => item.result === 'wrong');
  }

  function collectAllMistakes() {
    return words
      .map((word, i) => ({ word, result: wordResults[i]?.result }))
      .filter(item => item.result === 'wrong');
  }

  function _triggerExit() {
    if (collectAllMistakes().length > 0) setShowExitMistakes(true);
    else onExit?.();
  }

  return {
    words, wordResults, stats,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showConfirmReset, setShowConfirmReset,
    reset: _reset, resetPage, updateResult,
    collectPageMistakes, collectAllMistakes,
    triggerExit: _triggerExit,
    onExit,
    ...pagination,
  };
}
