import { useId, useLayoutEffect, useRef, useState } from "react";
import FormattingToolbar from "./FormattingToolbar";
import { formatSelection } from "./editorTools";
import "./contentEditors.css";

export default function FormattedText({ label, value, onChange, placeholder, compact = false, singleLine = false, lineTools = true }) {
  const id = useId();
  const field = useRef(null);
  const pendingSelection = useRef(null);
  const [linkOpen, setLinkOpen] = useState(false);
  useLayoutEffect(() => {
    const selection = pendingSelection.current;
    if (!selection || !field.current) return;
    pendingSelection.current = null;
    field.current.focus({preventScroll:true});
    field.current.setSelectionRange(selection.start, selection.end);
    field.current.scrollTop = selection.scrollTop;
  }, [value]);
  function action(kind, url) {
    const node = field.current;
    if (!node) return;
    const next = formatSelection(value, node.selectionStart, node.selectionEnd, kind, url);
    if (next.value === value) { node.focus({preventScroll:true}); node.setSelectionRange(next.start, next.end); return; }
    pendingSelection.current = {...next, scrollTop:node.scrollTop};
    onChange(next.value);
  }
  return <div className={`formatted-field ${compact ? "is-compact" : ""} ${singleLine ? "is-single-line" : ""}`}>
    <label htmlFor={id}>{label}</label>
    <div className="formatted-input">
      <FormattingToolbar label={label} onAction={action} lineTools={lineTools && !singleLine} linkOpen={linkOpen} onLinkToggle={setLinkOpen} />
      <textarea ref={field} id={id} className={`${singleLine ? "formatted-single-line" : "markdown-editor"} ${compact ? "short" : ""}`} rows={singleLine ? 1 : compact ? 3 : 7} value={value} placeholder={placeholder} onChange={(event) => onChange(singleLine ? event.target.value.replace(/\n/g, " ") : event.target.value)} onKeyDown={(event) => {
        if (event.nativeEvent.isComposing) return;
        if ((event.ctrlKey || event.metaKey) && !event.altKey) {
          const key = event.code?.startsWith("Key") ? event.code.slice(3).toLowerCase() : event.key.toLowerCase();
          const kind = {b:"bold", i:"italic"}[key];
          if (kind) { event.preventDefault(); action(kind); }
          if (key === "k") { event.preventDefault(); setLinkOpen(true); }
        }
        if (singleLine && event.key === "Enter") event.preventDefault();
      }} />
    </div>
    {!compact && <small className="editor-hint">Выделите текст и выберите оформление · Ctrl+B — жирный · Ctrl+I — курсив</small>}
  </div>;
}
