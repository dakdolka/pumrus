export const TRAINER_TYPE_LABELS = {
  options:    'Опции',
  stress:     'Ударения',
  dictionary: 'Словарные',
  input:      'Ввод',
};

export const PAGE_SIZE = 50;

// ── Ключ для localStorage ─────────────────────────────────
export function getStorageKey(trainerType, taskId) {
  return `trainer_${trainerType}_${taskId}`;
}

// ── Перемешать массив (Fisher-Yates) ──────────────────────
export function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ── Сохранить состояние в localStorage ───────────────────
export function saveState(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn('saveState failed', e);
  }
}

// ── Загрузить состояние из localStorage ──────────────────
export function loadState(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.warn('loadState failed', e);
    return null;
  }
}

// ── Для обратной совместимости ────────────────────────────
export function adaptItems(trainerType, items) {
  return items;
}
