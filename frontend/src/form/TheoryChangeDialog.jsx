import { useEffect, useMemo, useRef, useState } from "react";
import { TheoryDocument } from "../theory/TheoryRenderer";
import { editPackageBlock, parseTheoryEdit, prettyPackage } from "./theoryEdit";
import "./theoryChanges.css";

export default function TheoryChangeDialog({ documentId, owner, exerciseSets, api, inspector, onApplied, onClose, localDirty }) {
  const Inspector = inspector;
  const dialog = useRef(null);
  const [source, setSource] = useState("");
  const [expected, setExpected] = useState(null);
  const [examples, setExamples] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [help, setHelp] = useState(false);
  const initialSource = useRef("");
  const codeRef = useRef(null);
  const parsed = useMemo(() => {
    if (!source || !expected) return {result:null, error:""};
    try { return {result:parseTheoryEdit(source, expected), error:""}; }
    catch (reason) { return {result:null, error:reason.message}; }
  }, [source, expected]);
  const result = parsed.result;
  const selectedBlock = result?.blocks.find((block) => block.id === selectedId);

  useEffect(() => {
    dialog.current.showModal();
    const overflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    return () => { window.document.body.style.overflow = overflow; };
  }, []);
  useEffect(() => {
    let active = true;
    api(`/theory-documents/${documentId}/edit-package`).then((data) => {
      if (!active) return;
      const code = prettyPackage(data.package);
      setExpected(data.package); setExamples(data.examples); setSource(code); initialSource.current = code;
    }).catch((reason) => { if (active) setError(reason.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [documentId]);
  useEffect(() => {
    const stop = (event) => { if (source && source !== initialSource.current) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", stop);
    return () => window.removeEventListener("beforeunload", stop);
  }, [source]);

  async function loadExample(key) {
    setLoading(true); setError(""); setNotice("");
    try {
      const data = await api(`/theory-documents/${documentId}/edit-package?example=${encodeURIComponent(key)}`);
      // A fresh base is displayed together with the example, never an older snapshot.
      setExpected(data.package); setSource(prettyPackage(data.package)); setSelectedId(null);
    } catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }
  async function exportTheme() {
    setLoading(true); setError("");
    try {
      const data = await api(`/theory-documents/${documentId}/edit-package`);
      setExpected(data.package); setExamples(data.examples);
      const url = URL.createObjectURL(new Blob([prettyPackage(data.package)], {type:"application/json"}));
      const link = window.document.createElement("a");
      link.href = url; link.download = `pumrus-topic-${documentId}.json`; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice("Текущая тема выгружена. Ваш код в поле сохранён.");
    } catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(source); setNotice("Код скопирован"); }
    catch { codeRef.current?.focus(); codeRef.current?.select(); setNotice("Код выделен — скопируйте его"); }
  }
  function jumpToAfter() {
    const field = codeRef.current;
    const match = /"after"\s*:/.exec(source);
    if (!field || !match) return;
    field.focus(); field.setSelectionRange(match.index, match.index);
    const lineHeight = Number.parseFloat(window.getComputedStyle(field).lineHeight) || 20;
    field.scrollTop = source.slice(0, match.index).split("\n").length * lineHeight - lineHeight;
    field.scrollLeft = 0;
  }
  function updateBlock(id, patch) {
    if (!result) return;
    setSource(prettyPackage(editPackageBlock(result.package, id, patch)));
    setError("");
  }
  function removeBlock(id) {
    if (!result) return;
    setSource(prettyPackage(editPackageBlock(result.package, id, {}, true)));
    setSelectedId(null);
  }
  function close() {
    if (busy) return;
    if (source !== initialSource.current && !window.confirm("Закрыть окно? Скопируйте код, если хотите сохранить неподтверждённые правки.")) return;
    onClose();
  }
  async function apply() {
    if (!result?.changed || busy || localDirty) return;
    setBusy(true); setError("");
    try {
      const saved = await api(`/theory-documents/${documentId}/apply-package`, {method:"POST", body:JSON.stringify(result.package)});
      initialSource.current = source;
      onApplied(saved, result.package.after);
    } catch (reason) {
      setError(reason.message);
      if (reason.status === 409) {
        // Refresh the comparison base, preserving the user's code for manual rebasing.
        try { const data = await api(`/theory-documents/${documentId}/edit-package`); setExpected(data.package); }
        catch { /* Keep the actionable publication error if refreshing is unavailable. */ }
      }
    }
    finally { setBusy(false); }
  }
  function page(value, blocks, after) {
    return <section className={`change-page ${after ? "change-after" : "change-before"}`} aria-label={after ? "Страница после изменений" : "Страница до изменений"}>
      <header className="change-page-label"><strong>{after ? "После" : "До"}</strong><span>{after ? "Нажмите на блок, чтобы отредактировать" : "Текущая опубликованная версия"}</span></header>
      <div className="change-page-scroll"><div className="preview-device">
        <header><span>Задание {owner.taskNumber}</span><h1>{value.ownerTitle}</h1>{value.description && <p>{value.description}</p>}</header>
        <TheoryDocument document={{blocks}} selectedBlockId={after ? selectedId : null} onBlockClick={after && !busy && !loading ? (id) => setSelectedId(String(id)) : undefined}
          onAuthorNoteChange={after && !busy && !loading ? (id, patch) => { const block = result.blocks.find((b) => b.id === String(id)); if (block) updateBlock(String(id), {settings:{...block.settings, ...patch}}); } : undefined} />
      </div></div>
    </section>;
  }

  return <dialog ref={dialog} className="theory-change-dialog" aria-labelledby="theory-change-title" onCancel={(event) => {event.preventDefault(); close();}}>
    <header className="change-dialog-header"><div><span className="overline">{owner.title}</span><h2 id="theory-change-title">Изменения по коду</h2></div><button className="button" disabled={busy} onClick={close} aria-label="Закрыть изменения по коду">Закрыть</button></header>
    <div className="change-dialog-body">
      <div className="change-code-actions"><button className="button" disabled={loading || busy || !expected} onClick={exportTheme}>Экспорт темы</button><button className="button" disabled={busy || !source} onClick={copy}>Скопировать код</button><button className="button" aria-expanded={help} onClick={() => setHelp(!help)}>Как устроен код</button>
        {examples.map((example) => <button className="button" key={example.key} disabled={loading || busy} onClick={() => loadExample(example.key)}>Пример: {example.title}</button>)}
      </div>
      {help && <div className="change-help"><p><code>base</code> — версия исходной темы, <code>before</code> — исходная страница. Оставьте их как есть. Все правки вносите в <code>after</code>.</p><p><code>after.blocks</code> — блоки в порядке показа; <code>children</code> — вложенные блоки. <code>type</code> задаёт вид, <code>data</code> — содержимое, <code>settings</code> — оформление. Новый блок можно добавить без <code>id</code>.</p><pre>{'{ "type": "callout", "data": { "variant": "rule", "markdown": "**Правило:** ваш текст" } }'}</pre><p>В тексте работают <code>**жирный**</code>, <code>*курсив*</code> и <code>\n</code> для новой строки. Таблица: <code>{'"rows": [{"cells": ["Первая ячейка", "Вторая"]}]'}</code>. Название темы: <code>after.ownerTitle</code>.</p></div>}
      <div className="change-code-heading"><label className="change-code-label" htmlFor="theory-change-code">Код изменений · JSON</label><button className="button" disabled={loading || busy || !source} onClick={jumpToAfter}>Перейти к after</button></div>
      <textarea ref={codeRef} id="theory-change-code" className="change-code" spellCheck={false} value={source} disabled={loading || busy} onChange={(event) => {setSource(event.target.value); setSelectedId(null); setError(""); setNotice("");}} placeholder={loading ? "Экспортируем выбранную тему…" : "Вставьте JSON-пакет с изменениями"} />
      {(parsed.error || error) && <p className="change-error" role="alert">{parsed.error || error}</p>}
      {notice && <p role="status">{notice}</p>}
      {localDirty && <p className="change-error">В обычном редакторе есть неопубликованные изменения. Опубликуйте их перед применением пакета, затем экспортируйте тему заново.</p>}
      {result && <div className={`change-preview-layout ${selectedBlock ? "has-inspector" : ""}`}>
        {page(result.package.before, result.before.blocks, false)}
        {page(result.package.after, result.after.blocks, true)}
        {selectedBlock && <section className="change-inspector" aria-label="Редактирование блока результата"><button className="button" onClick={() => setSelectedId(null)}>Завершить правку блока</button><fieldset disabled={busy || loading}><Inspector key={selectedBlock.id} block={selectedBlock} update={updateBlock} remove={removeBlock} exerciseSets={exerciseSets} currentOwner={owner} /></fieldset></section>}
      </div>}
    </div>
    <footer className="change-dialog-footer"><p>{result?.changed ? "Будет создана новая опубликованная версия. Предыдущая сохранится в истории." : "Измените after или вставьте подготовленный пакет."}</p><button className="button primary" disabled={busy || loading || !result?.changed || !result.after.blocks.length || localDirty} onClick={apply}>{busy ? "Применяем…" : "Применить изменения"}</button></footer>
  </dialog>;
}
