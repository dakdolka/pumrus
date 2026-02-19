import { useState, useEffect } from 'react';
import { shuffleArray, loadState, saveState } from '../trainerUtils.js';
import { useTrainerPagination } from './useTrainerPagination.js';

export function useLetterTrainer({ storageKey, rawData, parseWord, onExit }) {
  const [words,         setWords]         = useState([]);
  const [letterStates,  setLetterStates]  = useState([]);
  const [stats,         setStats]         = useState({ total: 0, correct: 0, wrong: 0 });
  const [currentWord,   setCurrentWord]   = useState(0);
  const [currentLetter, setCurrentLetter] = useState(0);
  const [showPageMistakes, setShowPageMistakes] = useState(false);
  const [showAllMistakes,  setShowAllMistakes]  = useState(false); // пункт 4/5
  const [showExitMistakes, setShowExitMistakes] = useState(false);
  const [showConfirmReset, setShowConfirmReset] = useState(false);

  const pagination = useTrainerPagination({
    items: letterStates,
    isPageDone: slice => slice.every(ws => ws.every(ls => ls.done)),
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
      setLetterStates(saved.letterStates ?? []);
      setStats(saved.stats ?? { total: 0, correct: 0, wrong: 0 });
      setCurrentWord(saved.currentWord ?? 0);
      setCurrentLetter(saved.currentLetter ?? 0);
      setCurrentPage(saved.currentPage ?? 0);
      initShownPages(saved.letterStates ?? []);
    } else {
      _reset();
    }
  }, []);

  useEffect(() => {
    if (words.length > 0) {
      saveState(storageKey, { words, letterStates, stats, currentWord, currentLetter, currentPage });
    }
  }, [words, letterStates, stats, currentWord, currentLetter, currentPage]);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;
    const handleBack = () => {
      if (currentPage > 0) setCurrentPage(p => p - 1);
      else _triggerExit();
    };
    tg.onEvent('backButtonClicked', handleBack);
    return () => tg.offEvent?.('backButtonClicked', handleBack);
  }, [currentPage, letterStates]);

  useEffect(() => {
    for (let w = start; w < end; w++) {
      const idx = letterStates[w]?.findIndex(ls => !ls.done) ?? -1;
      if (idx !== -1) { setCurrentWord(w); setCurrentLetter(idx); return; }
    }
    setCurrentWord(start);
    setCurrentLetter(0);
  }, [currentPage]);

  function _reset() {
    if (!rawData?.length) return;
    const shuffled = shuffleArray(rawData.map(parseWord));
    const states   = shuffled.map(word => word.check.map(() => ({ done: false, correct: null, input: '' })));
    setWords(shuffled);
    setLetterStates(states);
    setStats({ total: shuffled.reduce((s, w) => s + w.check.length, 0), correct: 0, wrong: 0 });
    setCurrentWord(0);
    setCurrentLetter(0);
    setCurrentPage(0);
    resetShownPages();
    localStorage.removeItem(storageKey);
  }

  function resetPage() {
    let pageCorrect = 0, pageWrong = 0;
    for (let i = start; i < end; i++) {
      letterStates[i]?.forEach(ls => {
        if (ls.done && ls.correct)  pageCorrect++;
        if (ls.done && !ls.correct) pageWrong++;
      });
    }
    const newStates = [...letterStates];
    for (let i = start; i < end; i++) {
      newStates[i] = words[i].check.map(() => ({ done: false, correct: null, input: '' }));
    }
    setLetterStates(newStates);
    setStats(prev => ({ ...prev, correct: prev.correct - pageCorrect, wrong: prev.wrong - pageWrong }));
    setCurrentWord(start);
    setCurrentLetter(0);
    allowPageAgain();
  }

  function focusFirstEmpty() {
    for (let w = start; w < end; w++) {
      const idx = letterStates[w]?.findIndex(ls => !ls.done) ?? -1;
      if (idx !== -1) { setCurrentWord(w); setCurrentLetter(idx); return; }
    }
  }

  function updateLetterState(wordIndex, letterIndex, newState, isCorrect) {
    const newStates = [...letterStates];
    newStates[wordIndex] = [...newStates[wordIndex]];
    newStates[wordIndex][letterIndex] = newState;
    setLetterStates(newStates);
    setStats(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      wrong:   prev.wrong   + (isCorrect ? 0 : 1),
    }));
    return newStates;
  }

  function _collectMistakesFrom(statesSlice, wordsSlice) {
    return wordsSlice.map((word, i) => {
      if (!statesSlice[i]?.some(ls => ls.done && !ls.correct)) return null;
      return [...word.lower].map((ch, j) =>
        word.check.includes(j)
          ? { char: ch.toUpperCase(), highlight: true }
          : { char: ch, highlight: false }
      );
    }).filter(Boolean);
  }

  function collectPageMistakes() {
    return _collectMistakesFrom(letterStates.slice(start, end), words.slice(start, end));
  }

  function collectAllMistakes() {
    return _collectMistakesFrom(letterStates, words);
  }

  function _triggerExit() {
    if (collectAllMistakes().length > 0) setShowExitMistakes(true);
    else onExit?.();
  }

  return {
    words, letterStates, stats,
    currentWord, setCurrentWord,
    currentLetter, setCurrentLetter,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showConfirmReset, setShowConfirmReset,
    reset: _reset, resetPage, focusFirstEmpty, updateLetterState,
    collectPageMistakes, collectAllMistakes,
    triggerExit: _triggerExit,
    onExit,
    ...pagination,
  };
}
