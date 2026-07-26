import { useEffect, useMemo, useRef, useState } from "react";
import { TheoryDocument, buildTheoryTree } from "../theory/TheoryRenderer";
import BrandLogo from "../BrandLogo";
import "./form.css";

const BLOCK_TYPES = [
  ["rich_text", "Текст"], ["section", "Группа"], ["callout", "Выноска"],
  ["example", "Пример"], ["list", "Список"], ["table", "Таблица"],
  ["image", "Изображение"], ["video_embed", "Видео"],
];
const CALLOUTS = [
  ["note", "Примечание"], ["rule", "Правило"], ["warning", "Предупреждение"],
  ["important", "Важно"], ["tip", "Подсказка"],
];

async function adminApi(path, options = {}) {
  const token = sessionStorage.getItem("umrus:admin-key") || "";
  const response = await fetch(`/api/v2/admin${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { "X-Admin-Key": token } : {}), ...(options.headers || {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = new Error(payload?.detail || "Не удалось выполнить запрос");
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

function makeId() {
  return `local-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`}`;
}
function normalizeBlocks(blocks = []) {
  const flat = [];
  const walk = (items, parentId = null) => items.forEach((item, index) => {
    const id = String(item.id);
    flat.push({ ...item, id, parentId: item.parentId == null ? parentId : String(item.parentId), sortOrder: item.sortOrder ?? index, children: undefined });
    if (item.children?.length) walk(item.children, id);
  });
  walk(blocks);
  return flat;
}
function signature(value) {
  return JSON.stringify(value);
}
function defaultData(type, previous = {}) {
  const markdown = previous.markdown || "";
  if (type === "section") return { title: previous.title || markdown || "Новая группа" };
  if (type === "list") return { style: "unordered", items: previous.items || (markdown ? markdown.split("\n") : ["Новый пункт"]) };
  if (type === "table") return { rows: previous.rows || [{ cells: ["Ячейка"] }] };
  if (type === "image") return { url: previous.url || "", alt: previous.alt || "", caption: previous.caption || "" };
  if (type === "video_embed") return { url: previous.url || "" };
  if (type === "callout") return { markdown: markdown || previous.title || "", variant: previous.variant || "note" };
  return { markdown: markdown || previous.title || "" };
}

export default function FormApp() {
  const [access, setAccess] = useState({ loading: true, allowed: false, required: false, error: "" });
  async function verify(key = null) {
    if (key !== null) sessionStorage.setItem("umrus:admin-key", key);
    try {
      const status = await adminApi("/status");
      if (status.requiresAuth) await adminApi("/catalog");
      setAccess({ loading: false, allowed: true, required: status.requiresAuth, error: "" });
    } catch (error) {
      setAccess({ loading: false, allowed: false, required: true, error: error.message });
    }
  }
  useEffect(() => {
    const telegram = window.Telegram?.WebApp;
    const applyTheme = () => {
      const theme = telegram?.initData
        ? (telegram.colorScheme === "light" ? "light" : "dark")
        : (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
      document.documentElement.dataset.theme = theme;
    };
    applyTheme();
    telegram?.onEvent?.("themeChanged", applyTheme);
    verify();
    return () => telegram?.offEvent?.("themeChanged", applyTheme);
  }, []);
  if (!access.allowed) return <AccessGate access={access} verify={verify} />;
  return <FormWorkspace />;
}

function FormWorkspace() {
  const [mode, setMode] = useState("theory");
  return <>
    <nav className="form-mode-tabs">
      <button className={mode === "theory" ? "active" : ""} onClick={() => setMode("theory")}>Теория</button>
      <button className={mode === "practice" ? "active" : ""} onClick={() => setMode("practice")}>Практика</button>
    </nav>
    {mode === "theory" ? <PocketEditor /> : <PracticeSettings />}
  </>;
}

function PracticeSettings() {
  const [sets, setSets] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    adminApi("/exercise-sets").then(setSets).catch((reason) => setError(reason.message));
  }, []);
  async function save(item) {
    try {
      await adminApi(`/exercise-sets/${item.id}/settings`, {
        method: "PATCH",
        body: JSON.stringify({ session_size: item.sessionSize, page_size: item.pageSize }),
      });
    } catch (reason) {
      setError(reason.message);
    }
  }
  function update(id, patch) {
    setSets((items) => items.map((item) => item.id === id ? { ...item, ...patch } : item));
  }
  return <main className="practice-form">
    <header><span className="overline">Карманная форма</span><h1>Настройки практики</h1>
      <p>Набор определяет размер тренировки и количество слов на одном экране.</p></header>
    {error && <p className="form-error">{error}</p>}
    <section className="practice-form-list">
      {sets.map((item) => <article key={item.id}>
        <div><small>Задание {item.taskNumber}{item.topicTitle ? ` · ${item.topicTitle}` : ""}</small>
          <strong>{item.title}</strong><span>{item.exerciseCount} упражнений · {(item.interactionTypes || []).join(", ")}</span></div>
        <label>Всего<input type="number" min="1" max="100" value={item.sessionSize}
          onChange={(event) => update(item.id, { sessionSize: Number(event.target.value) })} /></label>
        <label>В блоке<input type="number" min="1" max="20" value={item.pageSize}
          onChange={(event) => update(item.id, { pageSize: Number(event.target.value) })} /></label>
        <button className="button primary" onClick={() => save(item)}>Сохранить</button>
      </article>)}
    </section>
    <aside className="practice-types"><strong>Поддерживаемые типы</strong>
      <span>single_choice · stress_selection · vowel_fill · text_input</span>
      <small>Обычный ввод слова сохранён как отдельный тип; словарные слова используют vowel_fill.</small>
    </aside>
  </main>;
}

function AccessGate({ access, verify }) {
  const [key, setKey] = useState("");
  if (access.loading) return <main className="form-gate"><p>Открываем редактор…</p></main>;
  return <main className="form-gate"><section><Logo /><p className="overline">Редактор контента</p><h1>Вход в форму</h1><p>Введите ключ, заданный в <code>ADMIN_TOKEN</code>.</p><input autoFocus type="password" value={key} onChange={(e) => setKey(e.target.value)} onKeyDown={(e) => e.key === "Enter" && verify(key)} placeholder="Ключ доступа" />{access.error && <p className="form-error">{access.error}</p>}<button className="button primary" onClick={() => verify(key)}>Войти</button></section></main>;
}

function PocketEditor() {
  const [catalog, setCatalog] = useState(null);
  const [selected, setSelected] = useState(null);
  const [document, setDocument] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [ownerTitle, setOwnerTitle] = useState("");
  const [description, setDescription] = useState("");
  const [documentTitle, setDocumentTitle] = useState("");
  const [baseline, setBaseline] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [draggedId, setDraggedId] = useState(null);
  const [panel, setPanel] = useState("edit");
  const [catalogOpen, setCatalogOpen] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const currentState = useMemo(() => ({ blocks, ownerTitle, description, documentTitle }), [blocks, ownerTitle, description, documentTitle]);
  const dirty = Boolean(document) && signature(currentState) !== baseline;
  const tree = useMemo(() => buildTheoryTree(blocks), [blocks]);
  const selectedBlock = blocks.find((item) => item.id === selectedId);

  async function loadCatalog() {
    const data = await adminApi("/catalog");
    setCatalog(data);
    return data;
  }
  useEffect(() => { loadCatalog().catch((e) => setError(e.message)); }, []);
  useEffect(() => {
    const stop = (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", stop);
    return () => window.removeEventListener("beforeunload", stop);
  }, [dirty]);

  async function choose(owner) {
    if (dirty && !window.confirm("Отменить неопубликованные изменения?")) return;
    setSelected(owner); setSelectedId(null); setError(""); setPanel("edit");
    let doc = await adminApi(`/theory-documents?owner_type=${owner.type}&owner_id=${owner.id}`);
    if (!doc) {
      doc = await adminApi("/theory-documents", { method: "POST", body: JSON.stringify({ owner_type: owner.type, owner_id: owner.id, title: owner.title }) });
    }
    const next = { blocks: normalizeBlocks(doc.blocks), ownerTitle: owner.title, description: owner.shortDescription || "", documentTitle: doc.title || owner.title };
    setDocument(doc); setBlocks(next.blocks); setOwnerTitle(next.ownerTitle); setDescription(next.description); setDocumentTitle(next.documentTitle); setBaseline(signature(next));
    if (window.innerWidth < 820) setCatalogOpen(false);
  }

  function updateBlock(id, patch) {
    setBlocks((items) => items.map((item) => item.id === id ? { ...item, ...patch } : item));
  }
  function addBlock(parentId = null) {
    const siblings = blocks.filter((item) => item.parentId === parentId);
    const id = makeId();
    setBlocks((items) => [...items, { id, parentId, type: "rich_text", data: { markdown: "" }, settings: {}, sortOrder: siblings.length }]);
    setSelectedId(id);
    return id;
  }
  function removeBlock(id) {
    const doomed = new Set([id]);
    let changed = true;
    while (changed) {
      changed = false;
      blocks.forEach((item) => { if (item.parentId && doomed.has(item.parentId) && !doomed.has(item.id)) { doomed.add(item.id); changed = true; } });
    }
    if (!window.confirm(`Удалить блок${doomed.size > 1 ? " и все вложенные блоки" : ""}?`)) return;
    setBlocks((items) => items.filter((item) => !doomed.has(item.id)));
    setSelectedId(null);
  }
  function dropBefore(targetId) {
    if (!draggedId || draggedId === targetId) return;
    setBlocks((items) => {
      const target = items.find((item) => item.id === targetId);
      const moved = items.find((item) => item.id === draggedId);
      if (!target || !moved || isDescendant(items, target.parentId, draggedId)) return items;
      const siblings = items.filter((item) => item.parentId === target.parentId && item.id !== draggedId).sort((a, b) => a.sortOrder - b.sortOrder);
      const index = siblings.findIndex((item) => item.id === targetId);
      siblings.splice(index, 0, { ...moved, parentId: target.parentId });
      const order = new Map(siblings.map((item, i) => [item.id, i]));
      return items.map((item) => item.id === draggedId ? { ...item, parentId: target.parentId, sortOrder: order.get(item.id) } : order.has(item.id) ? { ...item, sortOrder: order.get(item.id) } : item);
    });
    setDraggedId(null);
  }
  function nestInside(parentId) {
    if (!draggedId || draggedId === parentId || isDescendant(blocks, parentId, draggedId)) return;
    const count = blocks.filter((item) => item.parentId === parentId && item.id !== draggedId).length;
    updateBlock(draggedId, { parentId, sortOrder: count });
    setDraggedId(null);
  }
  async function publish() {
    if (!blocks.length) { setError("Добавьте хотя бы один блок"); return; }
    setBusy(true); setError("");
    try {
      const payload = {
        title: documentTitle.trim() || ownerTitle.trim(),
        owner_title: ownerTitle.trim(),
        owner_description: description.trim() || null,
        blocks: blocks.map((item) => ({ client_id: item.id, parent_client_id: item.parentId, block_type: item.type, data: item.data || {}, settings: item.settings || {}, sort_order: item.sortOrder || 0 })),
      };
      const result = await adminApi(`/theory-documents/${document.id}/publish-live`, { method: "POST", body: JSON.stringify(payload) });
      const freshCatalog = await loadCatalog();
      const refreshedOwner = findOwner(freshCatalog, selected.type, selected.id) || { ...selected, title: ownerTitle, shortDescription: description };
      const next = { blocks: normalizeBlocks(result.blocks), ownerTitle: refreshedOwner.title, description: refreshedOwner.shortDescription || "", documentTitle: result.title };
      setDocument(result); setBlocks(next.blocks); setOwnerTitle(next.ownerTitle); setDescription(next.description); setDocumentTitle(next.documentTitle); setBaseline(signature(next)); setSelected({ ...selected, ...refreshedOwner });
      setNotice("Опубликовано"); setTimeout(() => setNotice(""), 2200);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  return <div className="form-app">
    <header className="form-header"><button className="icon-button" onClick={() => setCatalogOpen((v) => !v)} aria-label="Каталог">☰</button><Logo /><div className="publish-wrap">{dirty && <span>есть изменения</span>}<button className="button primary" disabled={!dirty || busy} onClick={publish}>{busy ? "Публикуем…" : "Опубликовать"}</button></div></header>
    <div className={`form-layout ${catalogOpen ? "" : "catalog-hidden"}`}>
      <Catalog catalog={catalog} selected={selected} choose={choose} />
      <main className="workspace">
        {!selected ? <Welcome /> : <>
          <div className="mobile-tabs"><button className={panel === "edit" ? "active" : ""} onClick={() => setPanel("edit")}>Редактор</button><button className={panel === "preview" ? "active" : ""} onClick={() => setPanel("preview")}>Предпросмотр</button></div>
          <section className={`edit-pane mobile-${panel}`}>
            <div className="owner-fields"><span className="overline">Задание {selected.taskNumber} · {selected.type === "topic" ? "тема" : "введение"}</span><input className="title-input" value={ownerTitle} onChange={(e) => setOwnerTitle(e.target.value)} /><textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Краткое описание" rows="2" /><input value={documentTitle} onChange={(e) => setDocumentTitle(e.target.value)} placeholder="Название документа" /></div>
            <div className="editing-body">
              <div className="structure-column">
                <div className="blocks-head"><div><span className="overline">Структура</span><strong>{blocks.length} блоков</strong></div><button className="button" onClick={() => addBlock()}>+ Блок</button></div>
                <div className="block-list">{tree.map((node) => <BlockNode key={node.id} node={node} depth={0} selectedId={selectedId} onSelect={setSelectedId} onDrag={setDraggedId} onDrop={dropBefore} onNest={nestInside} onAdd={addBlock} />)}</div>
              </div>
              {selectedBlock
                ? <BlockInspector key={selectedBlock.id} block={selectedBlock} update={updateBlock} remove={removeBlock} />
                : <aside className="inspector inspector-empty"><span className="overline">Редактор блока</span><p>Выберите блок или добавьте новый.</p></aside>}
            </div>
          </section>
          <section className={`preview-pane mobile-${panel}`}><div className="preview-label"><span>Предпросмотр</span><small>Так страницу увидит ученик</small></div><div className="preview-device"><header><span>Задание {selected.taskNumber}</span><h1>{ownerTitle}</h1>{description && <p>{description}</p>}</header><TheoryDocument document={{ blocks }} onBlockClick={(id) => { setSelectedId(String(id)); setPanel("edit"); }} /></div></section>
        </>}
      </main>
    </div>
    {notice && <div className="toast">{notice}</div>}{error && <button className="global-error" onClick={() => setError("")}>{error}</button>}
  </div>;
}

function Catalog({ catalog, selected, choose }) {
  return <aside className="catalog"><p className="overline">{catalog?.courseVersion?.title || "Теория"}</p><h2>Содержание</h2><div className="catalog-list">{catalog?.tasks?.map((task) => <div key={task.id} className="catalog-task"><button className={selected?.type === "task" && selected.id === task.id ? "active" : ""} onClick={() => choose({ ...task, type: "task", taskNumber: task.number })}><b>{task.number}</b><span>{task.title}</span></button>{task.topics.map((topic) => <button key={topic.id} className={`topic ${selected?.type === "topic" && selected.id === topic.id ? "active" : ""}`} onClick={() => choose({ ...topic, type: "topic", taskNumber: task.number })}>{topic.title}</button>)}</div>)}</div></aside>;
}
function Welcome() { return <section className="welcome"><Logo /><p className="overline">Карманная форма</p><h1>Выберите задание или тему</h1><p>Редактируйте блоки слева и сразу смотрите итоговую страницу. На сервер изменения попадут только после публикации.</p></section>; }
function Logo() { return <a className="form-logo" href="/"><BrandLogo className="form-brand-logo" /></a>; }

function BlockNode({ node, depth, selectedId, onSelect, onDrag, onDrop, onNest, onAdd }) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = Boolean(node.children?.length);
  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const bounds = event.currentTarget.getBoundingClientRect();
    const position = (event.clientY - bounds.top) / bounds.height;
    if (position < .25) onDrop(node.id);
    else {
      onNest(node.id);
      setExpanded(true);
    }
  }
  function addChild() {
    setExpanded(true);
    onAdd(node.id);
  }
  return <div className="tree-node">
    <div className={`block-row type-${node.type} variant-${node.data?.variant || "default"} ${selectedId === node.id ? "active" : ""}`} style={{ "--depth": depth }} draggable onDragStart={() => onDrag(node.id)} onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
      <button className="drag-handle" aria-label="Перетащить">⠿</button><button className="block-select" onClick={() => onSelect(node.id)}><small>{label(node.type)}</small><strong>{excerpt(node)}</strong></button>
      {hasChildren ? <button className={`tree-toggle ${expanded ? "open" : ""}`} onClick={() => setExpanded((value) => !value)} aria-label={expanded ? "Свернуть группу" : "Развернуть группу"}>›</button> : <span />}
      <button className="add-child" onClick={addChild} title="Добавить вложенный блок">+</button>
    </div>
    {expanded && node.children?.map((child) => <BlockNode key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} onDrag={onDrag} onDrop={onDrop} onNest={onNest} onAdd={onAdd} />)}
  </div>;
}

function BlockInspector({ block, update, remove }) {
  const editorRef = useRef(null);
  const setData = (patch) => update(block.id, { data: { ...(block.data || {}), ...patch } });
  function changeType(type) { update(block.id, { type, data: defaultData(type, block.data) }); }
  useEffect(() => {
    const field = editorRef.current?.querySelector(".markdown-editor, input:not([type]), textarea");
    field?.focus();
  }, [block.id]);
  return <aside className="inspector" ref={editorRef}><div className="inspector-head"><div><span className="overline">Редактор блока</span><h2>{label(block.type)}</h2></div><button className="danger" onClick={() => remove(block.id)}>Удалить</button></div>
    <label>Тип<select value={block.type} onChange={(e) => changeType(e.target.value)}>{BLOCK_TYPES.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>
    <BlockFields block={block} setData={setData} update={update} />
  </aside>;
}
function BlockFields({ block, setData, update }) {
  if (["rich_text", "callout", "example"].includes(block.type)) return <>{block.type === "callout" && <label>Вид<select value={block.data?.variant || "note"} onChange={(e) => setData({ variant: e.target.value })}>{CALLOUTS.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>}<label>Содержание · Markdown<textarea className="markdown-editor" value={block.data?.markdown || ""} onChange={(e) => setData({ markdown: e.target.value })} placeholder="**Жирный**, *курсив*, списки, ссылки…" /></label>{block.type === "rich_text" && <label>Стиль<select value={block.settings?.variant || "paragraph"} onChange={(e) => update(block.id, { settings: { ...(block.settings || {}), variant: e.target.value } })}><option value="paragraph">Обычный текст</option><option value="heading_1">Заголовок</option><option value="heading_2">Подзаголовок</option></select></label>}</>;
  if (block.type === "section") return <label>Название группы · Markdown<input value={block.data?.title || ""} onChange={(e) => setData({ title: e.target.value })} /></label>;
  if (block.type === "list") return <><label>Вид<select value={block.data?.style || "unordered"} onChange={(e) => setData({ style: e.target.value })}><option value="unordered">Маркированный</option><option value="ordered">Нумерованный</option></select></label><label>Пункты · один на строку<textarea className="markdown-editor short" value={(block.data?.items || []).map((item) => item?.text || item).join("\n")} onChange={(e) => setData({ items: e.target.value.split("\n") })} /></label></>;
  if (block.type === "table") return <label>Таблица · строки с новой строки, ячейки через |<textarea className="markdown-editor short" value={(block.data?.rows || []).map((row) => (row?.cells || row || []).map((cell) => cell?.text || cell).join(" | ")).join("\n")} onChange={(e) => setData({ rows: e.target.value.split("\n").map((row) => ({ cells: row.split("|").map((cell) => cell.trim()) })) })} /></label>;
  if (block.type === "image") return <div className="field-stack"><label>Ссылка<input value={block.data?.url || ""} onChange={(e) => setData({ url: e.target.value })} /></label><label>Описание для доступности<input value={block.data?.alt || ""} onChange={(e) => setData({ alt: e.target.value })} /></label><label>Подпись · Markdown<input value={block.data?.caption || ""} onChange={(e) => setData({ caption: e.target.value })} /></label></div>;
  return <label>Ссылка на видео<input value={block.data?.url || ""} onChange={(e) => setData({ url: e.target.value })} /></label>;
}
function label(type) { return BLOCK_TYPES.find(([value]) => value === type)?.[1] || type; }
function excerpt(block) { return String(block.data?.title || block.data?.markdown || block.data?.url || "Пустой блок").replace(/[#*_`]/g, "").replace(/\s+/g, " ").slice(0, 55); }
function isDescendant(blocks, id, possibleAncestor) { let cursor = id; while (cursor) { if (cursor === possibleAncestor) return true; cursor = blocks.find((item) => item.id === cursor)?.parentId; } return false; }
function findOwner(catalog, type, id) { for (const task of catalog?.tasks || []) { if (type === "task" && task.id === id) return { ...task, type, taskNumber: task.number }; const topic = task.topics.find((item) => item.id === id); if (type === "topic" && topic) return { ...topic, type, taskNumber: task.number }; } return null; }
