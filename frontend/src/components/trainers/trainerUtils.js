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
