export const PAGE_SIZE = 50;

export function shuffleArray(arr) {
  return [...arr].sort(() => Math.random() - 0.5);
}

export function loadState(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

export function saveState(key, state) {
  try {
    localStorage.setItem(key, JSON.stringify(state));
  } catch {}
}

// Adapters: TaskItemBD[] → rawData формат каждого тренажёра
export function adaptItems(trainerType, items) {
  switch (trainerType) {
    case 'stress':
      return items.map(item => ({ question: item.raw, answer: item.raw }));
    case 'prefix':
    case 'dictionary':
      return items.map(item => item.raw);
    case 'spelling':
      return items.map(item => {
        try { return JSON.parse(item.raw); }
        catch { return { word: item.visible, correct: item.correct_option }; }
      });
    default:
      return items;
  }
}

export function getStorageKey(trainerType, taskId) {
  return `${trainerType}_task_${taskId}_v1`;
}
