import { useState, useEffect, useRef } from 'react';
import { PAGE_SIZE } from '../trainerUtils.js';

export function useTrainerPagination({ items, isPageDone, onPageComplete }) {
  const [currentPage, setCurrentPage] = useState(0);
  const [shownPages,  setShownPages]  = useState(new Set());

  // ref чтобы isPageDone не вызывал stale closure в эффекте
  const isPageDoneRef = useRef(isPageDone);
  isPageDoneRef.current = isPageDone;

  const start      = currentPage * PAGE_SIZE;
  const end        = Math.min(start + PAGE_SIZE, items.length);
  const totalPages = Math.ceil(items.length / PAGE_SIZE) || 1;
  const pageSlice  = items.slice(start, end);

  // Детект завершения страницы — срабатывает при каждом изменении items
  useEffect(() => {
    if (pageSlice.length === 0 || shownPages.has(currentPage)) return;
    if (isPageDoneRef.current(pageSlice)) {
      setShownPages(prev => new Set([...prev, currentPage]));
      onPageComplete?.();
    }
  }, [items]);

  // Вызывается при загрузке из localStorage — помечаем уже пройденные страницы
  function initShownPages(allItems) {
    const pgCount = Math.ceil(allItems.length / PAGE_SIZE);
    const done = new Set();
    for (let p = 0; p < pgCount; p++) {
      const slice = allItems.slice(p * PAGE_SIZE, (p + 1) * PAGE_SIZE);
      if (slice.length > 0 && isPageDoneRef.current(slice)) done.add(p);
    }
    setShownPages(done);
  }

  // Разрешить попапу показаться снова для текущей страницы (после resetPage)
  function allowPageAgain() {
    setShownPages(prev => {
      const next = new Set(prev);
      next.delete(currentPage);
      return next;
    });
  }

  // Полный сброс (после reset всего тренажёра)
  function resetShownPages() {
    setShownPages(new Set());
  }

  return {
    currentPage, setCurrentPage,
    start, end, totalPages, pageSlice,
    initShownPages, allowPageAgain, resetShownPages,
  };
}
