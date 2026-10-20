import { useState } from "react";

const INLINE = [["bold", "Жирный", "B", "Ctrl+B"], ["italic", "Курсив", "I", "Ctrl+I"], ["strike", "Зачёркнутый", "S", ""], ["code", "Фрагмент кода", "</>", ""]];

export default function FormattingToolbar({ label, onAction, lineTools = false, linkOpen, onLinkToggle, onUndo, onRedo, canUndo, canRedo }) {
  const [url, setUrl] = useState("https://");
  const [error, setError] = useState("");
  function addLink() {
    try { onAction("link", url); setError(""); onLinkToggle(false); }
    catch (reason) { setError(reason.message); }
  }
  return <>
    <div className="format-toolbar" role="toolbar" aria-label={`Оформление: ${label}`}>
      {INLINE.map(([action, name, symbol, shortcut]) => <button type="button" key={action} className={`format-${action}`} title={`${name}${shortcut ? ` (${shortcut})` : ""}`} aria-label={name} onMouseDown={(event) => event.preventDefault()} onClick={() => onAction(action)}>{symbol}</button>)}
      <button type="button" title="Добавить ссылку (Ctrl+K)" aria-label="Добавить ссылку" aria-expanded={linkOpen} onMouseDown={(event) => event.preventDefault()} onClick={() => onLinkToggle(!linkOpen)}>↗</button>
      {lineTools && <><span className="format-divider" /><button type="button" title="Маркированный список" aria-label="Маркированный список" onMouseDown={(e) => e.preventDefault()} onClick={() => onAction("bullet")}>• ≡</button><button type="button" title="Нумерованный список" aria-label="Нумерованный список" onMouseDown={(e) => e.preventDefault()} onClick={() => onAction("number")}>1. ≡</button><button type="button" title="Цитата" aria-label="Цитата" onMouseDown={(e) => e.preventDefault()} onClick={() => onAction("quote")}>❞</button></>}
      <button type="button" title="Убрать оформление выделенного текста" aria-label="Убрать оформление" onMouseDown={(e) => e.preventDefault()} onClick={() => onAction("clear")}>T×</button>
      {onUndo && <><span className="format-divider" /><button type="button" title="Отменить изменение таблицы (Ctrl+Z)" aria-label="Отменить изменение таблицы" disabled={!canUndo} onMouseDown={(e) => e.preventDefault()} onClick={onUndo}>↶</button><button type="button" title="Вернуть изменение таблицы (Ctrl+Shift+Z)" aria-label="Вернуть изменение таблицы" disabled={!canRedo} onMouseDown={(e) => e.preventDefault()} onClick={onRedo}>↷</button></>}
    </div>
    {linkOpen && <div className="format-link-editor"><label>Адрес ссылки<input autoFocus value={url} onChange={(event) => setUrl(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") {event.preventDefault(); addLink();} if (event.key === "Escape") {event.preventDefault(); event.stopPropagation(); onLinkToggle(false);} }} /></label><button type="button" className="button" onClick={addLink}>Вставить ссылку</button><button type="button" className="button" onClick={() => onLinkToggle(false)}>Отмена</button>{error && <p role="alert">{error}</p>}</div>}
  </>;
}
