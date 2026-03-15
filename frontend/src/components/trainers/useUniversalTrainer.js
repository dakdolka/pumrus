import { useState, useEffect, useRef } from 'react';
import { loadState, saveState, shuffleArray } from './trainerUtils.js';

export const PAGE_SIZE = 50;

export function resolveOptionSet(item, task) {
  if (item.option_set_override?.options?.length) return item.option_set_override;
  if (task.default_option_set?.options?.length)  return task.default_option_set;
  return null;
}

function isCorrect(chosenOption, item) {
  if (item.correct_option) return chosenOption.id === item.correct_option.id;
  return chosenOption.content.trim().toLowerCase() === item.content_correct.trim().toLowerCase();
}

async function apiInitSession(userId, taskId) {
  const r = await fetch('/api/tasks/sessions/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, task_id: taskId }),
  });
  return r.json();
}

async function apiCloseSession(sessionId) {
  await fetch(`/api/tasks/sessions/${sessionId}/close`, { method: 'POST' });
}

async function apiCreateMistake(userId, sessionId, itemId, chosenOptionId) {
  await fetch('/api/users/mistakes/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id:          userId,
      task_session_id:  sessionId,
      mistake_item_id:  itemId,
      chosen_option_id: chosenOptionId,
    }),
  }).catch(() => {});
}

async function apiGetOrCreateOption(content) {
  const r = await fetch('/api/tasks/general/options/get-or-create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  const data = await r.json();
  return data.option;
}

// ─────────────────────────────────────────────────────────────────────────────

export function useUniversalTrainer({ task, userId, storageKey, onExit, exitRef }) {
  const originalItems = task.items ?? [];

  const [shuffledItems, setShuffledItems] = useState([]);
  const [results,       setResults]       = useState([]);
  const [activeIndex,   setActiveIndex]   = useState(0);
  const [currentPage,   setCurrentPage]   = useState(0);
  const [sessionId,     setSessionId]     = useState(null);
  const [inputValue,    setInputValue]    = useState('');
  const [inputLoading,  setInputLoading]  = useState(false);

  const [showPageMistakes, setShowPageMistakes] = useState(false);
  const [showAllMistakes,  setShowAllMistakes]  = useState(false);
  const [showExitMistakes, setShowExitMistakes] = useState(false);
  const [showFinish,       setShowFinish]       = useState(false);
  const [showConfirmReset, setShowConfirmReset] = useState(false);
  const [isExiting,        setIsExiting]        = useState(false);

  const shownPagesRef = useRef(new Set());
  const sessionIdRef  = useRef(null);

  const items      = shuffledItems.length ? shuffledItems : originalItems;
  const totalPages = Math.ceil(items.length / PAGE_SIZE) || 1;
  const start      = currentPage * PAGE_SIZE;
  const end        = Math.min(start + PAGE_SIZE, items.length);

  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  // ── Mount ─────────────────────────────────────────────
  useEffect(() => {
    const saved = loadState(storageKey);
    if (
      saved?.sessionId &&
      saved?.shuffledItems?.length === originalItems.length &&
      saved?.results?.length === originalItems.length
    ) {
      setShuffledItems(saved.shuffledItems);
      setResults(saved.results);
      setCurrentPage(saved.currentPage ?? 0);
      setSessionId(saved.sessionId);
      shownPagesRef.current = new Set(saved.shownPages ?? []);
      setActiveIndex(_findNextUnanswered(saved.results, (saved.currentPage ?? 0) * PAGE_SIZE));
    } else {
      _startNewSession();
    }
  }, []);

  // ── Persist ───────────────────────────────────────────
  useEffect(() => {
    if (!sessionId || !shuffledItems.length) return;
    saveState(storageKey, {
      sessionId,
      shuffledItems,
      results,
      currentPage,
      shownPages: [...shownPagesRef.current],
    });
  }, [sessionId, shuffledItems, results, currentPage]);

  // ── exitRef ───────────────────────────────────────────
  useEffect(() => {
    if (exitRef) exitRef.current = _triggerExit;
  });

  // ── Детект завершения страницы / всего задания ────────
  useEffect(() => {
    if (!items.length || !results.length) return;
    const pageSlice = results.slice(start, end);
    if (!pageSlice.length) return;
    if (!pageSlice.every(r => r?.status && r.status !== 'none')) return;
    if (shownPagesRef.current.has(currentPage)) return;

    shownPagesRef.current.add(currentPage);

    if (results.every(r => r?.status && r.status !== 'none')) {
      _handleFinish();
    } else {
      setShowPageMistakes(true);
    }
  }, [results]);

  // ── Telegram BackButton ───────────────────────────────
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    const handle = () => {
      if (showFinish)       return;
      if (showConfirmReset) { setShowConfirmReset(false); return; }
      if (showExitMistakes) {
        setShowExitMistakes(false);
        if (isExiting) { setIsExiting(false); onExit?.(); }
        return;
      }
      if (showAllMistakes)  { setShowAllMistakes(false);  return; }
      if (showPageMistakes) { setShowPageMistakes(false); return; }
      if (currentPage > 0)  { setCurrentPage(p => p - 1); return; }
      _triggerExit();
    };

    tg.onEvent('backButtonClicked', handle);
    return () => tg.offEvent?.('backButtonClicked', handle);
  }, [
    showFinish, showConfirmReset, showExitMistakes,
    showAllMistakes, showPageMistakes, currentPage, isExiting,
  ]);

  // ── Helpers ───────────────────────────────────────────
  function _findNextUnanswered(res, fromAbs) {
    if (!res?.length) return 0;
    const s = Math.floor(fromAbs / PAGE_SIZE) * PAGE_SIZE;
    const e = Math.min(s + PAGE_SIZE, res.length);
    for (let i = fromAbs; i < e; i++) if (res[i]?.status === 'none') return i;
    for (let i = s; i < fromAbs; i++) if (res[i]?.status === 'none') return i;
    return fromAbs;
  }

  async function _startNewSession() {
    const shuffled = shuffleArray([...originalItems]);
    const emptyResults = shuffled.map(() => ({ status: 'none', notice: null, displayContent: null }));
    setShuffledItems(shuffled);
    setResults(emptyResults);
    setCurrentPage(0);
    setActiveIndex(0);
    setInputValue('');
    shownPagesRef.current = new Set();
    try {
      const sess = await apiInitSession(userId, task.id);
      setSessionId(sess.id);
    } catch (e) {
      console.error('Session init failed', e);
    }
  }

  // Завершение — сессию НЕ закрываем
  function _handleFinish() {
    localStorage.removeItem(storageKey);
    setShowFinish(true);
  }

  // Выход — сессию НЕ закрываем
  function _triggerExit() {
    const hasMistakes = results.some(r => r?.status === 'wrong');
    if (hasMistakes) { setIsExiting(true); setShowExitMistakes(true); }
    else onExit?.();
  }

  // ── Ответ через опцию ─────────────────────────────────
  async function answerWithOption(itemIndex, chosenOption) {
    const item   = items[itemIndex];
    if (!item) return;
    const ok     = isCorrect(chosenOption, item);
    const notice = ok ? (item.notice_right ?? null) : (item.notice_wrong ?? null);

    // displayContent — что показать в строке после ответа:
    // если правильно → content_correct, если неправильно → оставляем content_visible
    const displayContent = ok ? item.content_correct : null;

    const next = [...results];
    next[itemIndex] = { status: ok ? 'correct' : 'wrong', notice, displayContent };
    setResults(next);
    setInputValue('');

    if (!ok && sessionIdRef.current) {
      await apiCreateMistake(userId, sessionIdRef.current, item.id, chosenOption.id);
    }

    setActiveIndex(_findNextUnanswered(next, itemIndex + 1 < end ? itemIndex + 1 : start));
  }

  // ── Ответ через текст ─────────────────────────────────
  async function answerWithText(itemIndex, text) {
    if (!text.trim() || inputLoading) return;
    setInputLoading(true);
    try {
      const option = await apiGetOrCreateOption(text.trim());
      await answerWithOption(itemIndex, option);
    } catch (e) {
      console.error('Text answer failed', e);
    } finally {
      setInputLoading(false);
    }
  }

  // ── Сброс — единственное место где закрываем сессию ──
  async function reset() {
    setShowConfirmReset(false);
    const sid = sessionIdRef.current;
    if (sid) { try { await apiCloseSession(sid); } catch {} }
    localStorage.removeItem(storageKey);
    setSessionId(null);
    await _startNewSession();
  }

  // ── Сбор ошибок ───────────────────────────────────────
  function collectMistakes(from = 0, to = items.length) {
    return items.slice(from, to)
      .map((item, i) => ({ item, result: results[from + i] ?? { status: 'none', notice: null } }))
      .filter(({ result }) => result.status === 'wrong');
  }

  const stats = results.reduce(
    (acc, r) => {
      if (!r) return acc;
      if      (r.status === 'correct')  acc.correct++;
      else if (r.status === 'wrong')    acc.wrong++;
      else                              acc.remaining++;
      return acc;
    },
    { correct: 0, wrong: 0, remaining: 0 }
  );

  return {
    items, results, setResults, activeIndex, setActiveIndex,
    currentPage, setCurrentPage,
    totalPages, start, end,
    sessionId,
    inputValue, setInputValue, inputLoading,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showFinish,       setShowFinish,
    showConfirmReset, setShowConfirmReset,
    isExiting,
    stats,
    answerWithOption,
    answerWithText,
    reset,
    triggerExit: _triggerExit,
    collectMistakes,
    onExit,
  };
}
