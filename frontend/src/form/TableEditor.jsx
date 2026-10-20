import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import FormattingToolbar from "./FormattingToolbar";
import { cellText, changeTableColumn, columnName, formatSelection, parseClipboardTable, parseTable, pasteTableCells, rowCells, serializeTable, tableWidth, updateTableCell } from "./editorTools";
import "./contentEditors.css";

export default function TableEditor({ rows, onChange, settings = {} }) {
  const id = useId();
  const [mode, setMode] = useState("grid");
  const [raw, setRaw] = useState(() => serializeTable(rows));
  const [active, setActive] = useState([0, 0]);
  const [history, setHistory] = useState({past:[], future:[]});
  const [linkOpen, setLinkOpen] = useState(false);
  const fields = useRef(new Map());
  const source = useRef(null);
  const addRowButton = useRef(null);
  const pending = useRef(null);
  const emittedSignature = useRef(JSON.stringify(rows));
  const width = tableWidth(rows);
  const height = Math.max(1, rows.length);
  const row = Math.min(active[0], height - 1), column = Math.min(active[1], width - 1);

  useEffect(() => {
    const signature = JSON.stringify(rows);
    if (signature !== emittedSignature.current) {
      emittedSignature.current = signature;
      setRaw(serializeTable(rows));
      setHistory({past:[], future:[]});
    }
  }, [rows]);
  useLayoutEffect(() => {
    const selection = pending.current;
    if (!selection) return;
    const node = selection.source ? source.current : fields.current.get(`${selection.row}:${selection.column}`);
    if (!node) return;
    pending.current = null;
    node.focus({preventScroll:true});
    node.setSelectionRange(selection.start ?? node.value.length, selection.end ?? selection.start ?? node.value.length);
    if (selection.scrollTop !== undefined) node.scrollTop = selection.scrollTop;
    else node.scrollIntoView({block:"nearest", inline:"nearest"});
  }, [rows, active, mode, raw]);

  function emit(next, {rawText, record = true, settingsPatch} = {}) {
    const signature = JSON.stringify(next);
    if (rawText !== undefined) setRaw(rawText);
    else setRaw(serializeTable(next));
    if (signature === JSON.stringify(rows) && !settingsPatch) return;
    if (record) setHistory((current) => ({past:[...current.past.slice(-99), {rows, columnAlign:settings.columnAlign || [], tableHeader:settings.tableHeader !== false}], future:[]}));
    emittedSignature.current = signature;
    onChange(next, settingsPatch);
  }
  function focus(r, c, start, end) {
    pending.current = {row:r, column:c, start, end};
    setActive([r, c]);
  }
  function undo(redo = false) {
    const values = redo ? history.future : history.past;
    if (!values.length) return;
    const next = values.at(-1), current = {rows, columnAlign:settings.columnAlign || [], tableHeader:settings.tableHeader !== false};
    setHistory(redo ? {past:[...history.past, current], future:history.future.slice(0, -1)} : {past:history.past.slice(0, -1), future:[...history.future, current]});
    emit(next.rows, {record:false, settingsPatch:{columnAlign:next.columnAlign, tableHeader:next.tableHeader}});
    if (mode === "grid") focus(Math.min(row, Math.max(0, next.rows.length - 1)), Math.min(column, tableWidth(next.rows) - 1));
  }
  function addRow() {
    const next = rows.length ? [...rows] : [{cells:Array(width).fill("")}];
    next.splice(row + 1, 0, {cells:Array(width).fill("")});
    emit(next); focus(row + 1, column, 0, 0);
  }
  function addColumn() {
    const align = Array.from({length:width}, (_, c) => settings.columnAlign?.[c] || "left"); align.splice(column + 1, 0, "left");
    emit(changeTableColumn(rows.length ? rows : [{cells:[""]}], column + 1), {settingsPatch:{columnAlign:align}});
    focus(row, column + 1, 0, 0);
  }
  function removeColumn() {
    const align = Array.from({length:width}, (_, c) => settings.columnAlign?.[c] || "left"); align.splice(column, 1);
    emit(changeTableColumn(rows, column, true), {settingsPatch:{columnAlign:align}}); focus(row, Math.max(0, column - 1));
  }
  function format(action, url) {
    const node = mode === "source" ? source.current : fields.current.get(`${row}:${column}`);
    if (!node) return;
    const next = formatSelection(node.value, node.selectionStart, node.selectionEnd, action, url);
    if (mode === "source") {
      pending.current = {source:true, start:next.start, end:next.end, scrollTop:node.scrollTop};
      emit(parseTable(next.value), {rawText:next.value});
    } else {
      pending.current = {row, column, start:next.start, end:next.end, scrollTop:node.scrollTop};
      emit(updateTableCell(rows, row, column, next.value));
    }
    // Clearing an unformatted selection does not necessarily cause a render.
    if (next.value === node.value) { pending.current = null; node.focus({preventScroll:true}); node.setSelectionRange(next.start, next.end); }
  }
  function keyboard(event, r, c) {
    if (event.nativeEvent.isComposing) return;
    if ((event.ctrlKey || event.metaKey) && !event.altKey) {
      const key = event.code?.startsWith("Key") ? event.code.slice(3).toLowerCase() : event.key.toLowerCase();
      if (key === "b" || key === "i") {event.preventDefault(); format(key === "b" ? "bold" : "italic"); return;}
      if (key === "k") {event.preventDefault(); setLinkOpen(true); return;}
      if (key === "z" || key === "y") {if (mode === "grid") {event.preventDefault(); undo(key === "y" || event.shiftKey);} return;}
      if (event.key === "Enter" && mode === "grid") {event.preventDefault(); addRow(); return;}
    }
    if (mode === "source") {
      if (event.key === "Enter" && event.shiftKey) {
        event.preventDefault();
        const node = event.currentTarget, start = node.selectionStart;
        const next = raw.slice(0, start) + "\\n" + raw.slice(node.selectionEnd);
        pending.current = {source:true, start:start + 2, end:start + 2, scrollTop:node.scrollTop};
        emit(parseTable(next), {rawText:next});
      }
      return;
    }
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); addRowButton.current?.focus(); return; }
    if (event.key === "Tab" && !event.ctrlKey && !event.metaKey && !event.altKey) {
      const next = r * width + c + (event.shiftKey ? -1 : 1);
      if (next < 0) return;
      event.preventDefault();
      if (next >= height * width) emit([...(rows.length ? rows : [{cells:Array(width).fill("")}]), {cells:Array(width).fill("")}]);
      const nextRow = Math.floor(next / width), nextColumn = next % width;
      const value = cellText(rowCells(rows[nextRow])[nextColumn]);
      focus(nextRow, nextColumn, 0, value.length);
    }
  }

  return <section className="table-editor" aria-label="Редактор таблицы">
    <div className="table-editor-heading"><strong>Таблица <span>{height} × {width}</span></strong><div className="editor-segmented" aria-label="Режим редактирования таблицы"><button type="button" aria-pressed={mode === "grid"} onClick={() => {setMode("grid"); setLinkOpen(false);}}>Ячейки</button><button type="button" aria-pressed={mode === "source"} onClick={() => {if (mode === "source") return; setRaw(serializeTable(rows)); setMode("source"); setLinkOpen(false);}}>Текст с |</button></div></div>
    <FormattingToolbar label="Таблица" onAction={format} linkOpen={linkOpen} onLinkToggle={setLinkOpen} onUndo={() => undo()} onRedo={() => undo(true)} canUndo={!!history.past.length} canRedo={!!history.future.length} />
    {mode === "grid" ? <>
      <div className="table-grid-scroll"><table className="table-input-grid" style={{minWidth:32 + width * 140}}><thead><tr><th aria-label="Номер строки" />{Array.from({length:width}, (_, c) => <th key={c} className={column === c ? "is-active" : ""}><button type="button" aria-label={`Выбрать столбец ${columnName(c)}`} onClick={() => focus(row, c)}>{columnName(c)}</button></th>)}</tr></thead><tbody>
        {Array.from({length:height}, (_, r) => <tr key={r} className={r === 0 && settings.tableHeader !== false ? "is-header-row" : ""}><th className={row === r ? "is-active" : ""}><button type="button" aria-label={`Выбрать строку ${r + 1}`} onClick={() => focus(r, column)}>{r + 1}</button></th>{Array.from({length:width}, (_, c) => <td key={c} className={row === r && column === c ? "is-active" : ""}>
          <textarea ref={(node) => {if (node) fields.current.set(`${r}:${c}`, node); else fields.current.delete(`${r}:${c}`);}} className="table-cell-input" aria-label={`Ячейка ${columnName(c)}${r + 1}`} rows={Math.min(7, Math.max(2, cellText(rowCells(rows[r])[c]).split("\n").length))} style={{textAlign:settings.columnAlign?.[c] || "left"}} value={cellText(rowCells(rows[r])[c])} onFocus={() => setActive([r, c])} onChange={(event) => emit(updateTableCell(rows, r, c, event.target.value))} onKeyDown={(event) => keyboard(event, r, c)} onPaste={(event) => {
            const text = event.clipboardData.getData("text/plain");
            if (!text.includes("\t")) return;
            event.preventDefault();
            const matrix = parseClipboardTable(text);
            const next = pasteTableCells(rows, r, c, matrix);
            emit(next); focus(r + matrix.length - 1, c + matrix.at(-1).length - 1);
          }} />
        </td>)}</tr>)}
      </tbody></table></div>
      <div className="table-structure-actions"><button ref={addRowButton} type="button" className="button" onClick={addRow}>+ Строка</button><button type="button" className="button" onClick={addColumn}>+ Столбец</button><span className="table-current-cell">{columnName(column)}{row + 1}</span><button type="button" className="table-remove" disabled={height <= 1} onClick={() => {const next = rows.filter((_, index) => index !== row); emit(next); focus(Math.max(0, row - 1), column);}}>Убрать строку</button><button type="button" className="table-remove" disabled={width <= 1} onClick={removeColumn}>Убрать столбец</button></div>
      <div className="table-display-settings"><label><input type="checkbox" checked={settings.tableHeader !== false} onChange={(event) => emit(rows, {settingsPatch:{tableHeader:event.target.checked}})} />Первая строка — заголовок</label><label>Столбец {columnName(column)}<select aria-label="Выравнивание столбца" value={settings.columnAlign?.[column] || "left"} onChange={(event) => {const align = Array.from({length:width}, (_, c) => settings.columnAlign?.[c] || "left"); align[column] = event.target.value; emit(rows, {settingsPatch:{columnAlign:align}});}}><option value="left">По левому краю</option><option value="center">По центру</option><option value="right">По правому краю</option></select></label></div>
      <small className="editor-hint">Tab — следующая ячейка · Enter — перенос · Esc — выйти из ячеек · Вставка диапазона из Excel</small>
    </> : <><label className="table-source-label" htmlFor={id}>Строки через Enter, ячейки через |</label><textarea ref={source} id={id} className="markdown-editor table-source-input" value={raw} onChange={(event) => emit(parseTable(event.target.value), {rawText:event.target.value})} onKeyDown={keyboard} spellCheck={false} /><small className="editor-hint">Shift+Enter — перенос внутри ячейки · \| — символ | в тексте</small></>}
  </section>;
}
