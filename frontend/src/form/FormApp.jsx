import { useEffect, useMemo, useState } from "react";
import "./form.css";


const BLOCK_TYPES = [
  ["rich_text", "Текст"],
  ["section", "Подгруппа"],
  ["callout", "Выноска"],
  ["example", "Пример"],
  ["list", "Список"],
  ["table", "Таблица"],
  ["image", "Изображение"],
  ["video_embed", "Видео"],
];

const CALLOUT_VARIANTS = [
  ["note", "Примечание"],
  ["rule", "Правило"],
  ["warning", "Предупреждение"],
  ["important", "Важно"],
  ["tip", "Подсказка"],
];


async function adminApi(path, options = {}) {
  const token = sessionStorage.getItem("umrus:admin-key") || "";
  const response = await fetch(`/api/v2/admin${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Admin-Key": token } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = new Error(payload?.detail || "Не удалось выполнить запрос");
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}


function useAdminAccess() {
  const [state, setState] = useState({ loading: true, required: false, allowed: false, error: "" });

  async function verify(key = null) {
    if (key !== null) sessionStorage.setItem("umrus:admin-key", key);
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const status = await adminApi("/status");
      if (!status.requiresAuth) {
        setState({ loading: false, required: false, allowed: true, error: "" });
        return;
      }
      await adminApi("/catalog");
      setState({ loading: false, required: true, allowed: true, error: "" });
    } catch (error) {
      setState({
        loading: false,
        required: true,
        allowed: false,
        error: error.status === 401 ? "Неверный ключ" : error.message,
      });
    }
  }

  useEffect(() => { verify(); }, []);
  return { ...state, verify };
}


function AccessGate({ access }) {
  const [key, setKey] = useState("");
  if (access.loading) {
    return <div className="admin-gate"><span className="admin-loader" />Проверяем доступ…</div>;
  }
  return (
    <div className="admin-gate">
      <div className="gate-card">
        <div className="admin-brand"><span>У</span><strong>UmRus</strong></div>
        <p className="kicker">Редактор контента</p>
        <h1>Введите ключ доступа</h1>
        <p>Ключ задаётся переменной <code>ADMIN_TOKEN</code> на сервере.</p>
        <input
          type="password"
          value={key}
          autoFocus
          placeholder="Ключ"
          onChange={(event) => setKey(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && access.verify(key)}
        />
        {access.error && <div className="form-error">{access.error}</div>}
        <button className="primary-action" onClick={() => access.verify(key)}>Войти</button>
      </div>
    </div>
  );
}


export default function FormApp() {
  const access = useAdminAccess();
  if (!access.allowed) return <AccessGate access={access} />;
  return <TheoryAdmin />;
}


function TheoryAdmin() {
  const [catalog, setCatalog] = useState(null);
  const [selected, setSelected] = useState(null);
  const [document, setDocument] = useState(null);
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [loadingDocument, setLoadingDocument] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [mobilePanel, setMobilePanel] = useState("catalog");

  async function loadCatalog() {
    try {
      setCatalog(await adminApi("/catalog"));
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  useEffect(() => { loadCatalog(); }, []);
  useEffect(() => {
    const handle = (event) => {
      const message = event.reason?.message || "Неожиданная ошибка редактора";
      setError(message);
    };
    window.addEventListener("unhandledrejection", handle);
    return () => window.removeEventListener("unhandledrejection", handle);
  }, []);

  async function selectOwner(owner) {
    setSelected(owner);
    setSelectedBlockId(null);
    setMobilePanel("blocks");
    setLoadingDocument(true);
    setError("");
    try {
      const result = await adminApi(
        `/theory-documents?owner_type=${owner.type}&owner_id=${owner.id}`,
      );
      setDocument(result);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoadingDocument(false);
    }
  }

  async function refreshDocument() {
    if (!selected) return;
    const result = await adminApi(
      `/theory-documents?owner_type=${selected.type}&owner_id=${selected.id}`,
    );
    setDocument(result);
    return result;
  }

  function flash(message) {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 2200);
  }

  async function createTopic(task) {
    const title = window.prompt("Название новой темы");
    if (!title?.trim()) return;
    await adminApi("/topics", {
      method: "POST",
      body: JSON.stringify({
        exam_task_id: task.id,
        title: title.trim(),
        short_description: null,
      }),
    });
    await loadCatalog();
    flash("Тема создана");
  }

  const blocks = document?.blocks || [];
  const selectedBlock = blocks.find((block) => block.id === selectedBlockId) || null;
  const isDraft = document?.editingVersion?.status === "draft";

  return (
    <div className="admin-app">
      <header className="admin-header">
        <div className="admin-brand"><span>У</span><strong>UmRus</strong></div>
        <div>
          <p className="kicker">Контент</p>
          <h1>Теория</h1>
        </div>
        <div className="header-actions">
          <a href="/" target="_blank" rel="noreferrer" className="ghost-action">Открыть сайт</a>
          {selected && (
            <a
              href={selected.type === "topic"
                ? `/theory/tasks/${selected.taskNumber}/topics/${selected.id}`
                : `/theory/tasks/${selected.taskNumber}`}
              target="_blank"
              rel="noreferrer"
              className="ghost-action"
            >
              Предпросмотр
            </a>
          )}
        </div>
      </header>

      <nav className="mobile-tabs">
        {[
          ["catalog", "Раздел"],
          ["blocks", "Блоки"],
          ["editor", "Редактор"],
        ].map(([value, label]) => (
          <button
            key={value}
            className={mobilePanel === value ? "active" : ""}
            onClick={() => setMobilePanel(value)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="admin-workspace">
        <aside className={`catalog-panel mobile-${mobilePanel}`}>
          <div className="panel-heading">
            <div>
              <p className="kicker">{catalog?.courseVersion?.code || "—"}</p>
              <h2>Задания и темы</h2>
            </div>
            <button className="icon-action" onClick={loadCatalog} title="Обновить">↻</button>
          </div>
          {!catalog && <PanelLoading />}
          <div className="catalog-tree">
            {(catalog?.tasks || []).map((task) => (
              <details key={task.id} className="catalog-task">
                <summary>
                  <span>{task.number}</span>
                  <strong>{task.title}</strong>
                  <i>⌄</i>
                </summary>
                <div className="catalog-task-content">
                  <button
                    className={selected?.type === "task" && selected.id === task.id ? "owner-row active" : "owner-row"}
                    onClick={() => selectOwner({
                      type: "task",
                      id: task.id,
                      taskNumber: task.number,
                      title: task.title,
                      shortDescription: task.shortDescription,
                    })}
                  >
                    <span className="owner-kind">Введение</span>
                    <strong>Общая теория задания</strong>
                  </button>
                  {task.topics.map((topic) => (
                    <button
                      key={topic.id}
                      className={selected?.type === "topic" && selected.id === topic.id ? "owner-row active" : "owner-row"}
                      onClick={() => selectOwner({
                        type: "topic",
                        id: topic.id,
                        taskNumber: task.number,
                        title: topic.title,
                        shortDescription: topic.shortDescription,
                      })}
                    >
                      <span className="owner-kind">Тема</span>
                      <strong>{topic.title}</strong>
                    </button>
                  ))}
                  <button className="add-topic" onClick={() => createTopic(task)}>+ Добавить тему</button>
                </div>
              </details>
            ))}
          </div>
        </aside>

        <section className={`blocks-panel mobile-${mobilePanel}`}>
          {!selected ? (
            <EmptyPanel title="Выберите раздел" text="Слева находятся задания и связанные с ними темы." />
          ) : loadingDocument ? <PanelLoading /> : (
            <>
              <OwnerHeader
                selected={selected}
                document={document}
                isDraft={isDraft}
                onCatalogReload={loadCatalog}
                onDocumentReload={refreshDocument}
                onNotice={flash}
              />
              {!document ? (
                <CreateDocument selected={selected} onCreated={refreshDocument} />
              ) : (
                <>
                  <DocumentBar
                    document={document}
                    isDraft={isDraft}
                    onChanged={refreshDocument}
                    onNotice={flash}
                  />
                  <BlockTree
                    blocks={blocks}
                    selectedId={selectedBlockId}
                    onSelect={(id) => {
                      setSelectedBlockId(id);
                      setMobilePanel("editor");
                    }}
                    disabled={!isDraft}
                    documentId={document.id}
                    onChanged={async (id = null) => {
                      const updated = await refreshDocument();
                      if (id) setSelectedBlockId(id);
                      else if (selectedBlockId && !updated.blocks.some((block) => block.id === selectedBlockId)) {
                        setSelectedBlockId(null);
                      }
                    }}
                  />
                </>
              )}
            </>
          )}
        </section>

        <aside className={`editor-panel mobile-${mobilePanel}`}>
          {selectedBlock ? (
            <BlockEditor
              key={selectedBlock.id}
              block={selectedBlock}
              blocks={blocks}
              disabled={!isDraft}
              onSaved={async () => {
                await refreshDocument();
                flash("Блок сохранён");
              }}
            />
          ) : (
            <EmptyPanel title="Выберите блок" text="Настройки выбранного блока появятся здесь." compact />
          )}
        </aside>
      </div>
      {notice && <div className="toast">{notice}</div>}
      {error && <div className="global-error" onClick={() => setError("")}>{error}</div>}
    </div>
  );
}


function OwnerHeader({ selected, document, isDraft, onCatalogReload, onDocumentReload, onNotice }) {
  const [title, setTitle] = useState(selected.title);
  const [description, setDescription] = useState(selected.shortDescription || "");

  useEffect(() => {
    setTitle(selected.title);
    setDescription(selected.shortDescription || "");
  }, [selected]);

  async function save() {
    await adminApi(`/${selected.type === "task" ? "tasks" : "topics"}/${selected.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: title.trim(),
        short_description: description.trim() || null,
      }),
    });
    if (document && document.title !== title.trim() && isDraft) {
      // The document title remains intentionally version-independent for now.
      await onDocumentReload();
    }
    await onCatalogReload();
    onNotice("Название сохранено");
  }

  return (
    <div className="owner-header">
      <p className="kicker">Задание {selected.taskNumber} · {selected.type === "topic" ? "тема" : "введение"}</p>
      <input className="owner-title" value={title} onChange={(event) => setTitle(event.target.value)} />
      <textarea
        className="owner-description"
        value={description}
        placeholder="Краткое описание — необязательно"
        onChange={(event) => setDescription(event.target.value)}
      />
      <button className="text-action" onClick={save}>Сохранить название</button>
    </div>
  );
}


function CreateDocument({ selected, onCreated }) {
  const [creating, setCreating] = useState(false);
  async function create() {
    setCreating(true);
    try {
      await adminApi("/theory-documents", {
        method: "POST",
        body: JSON.stringify({
          owner_type: selected.type,
          owner_id: selected.id,
          title: selected.title,
        }),
      });
      await onCreated();
    } finally {
      setCreating(false);
    }
  }
  return (
    <EmptyPanel
      title="Теория ещё не создана"
      text="Создайте первый черновик документа для этого раздела."
      action={<button className="primary-action" onClick={create} disabled={creating}>
        {creating ? "Создаём…" : "Создать документ"}
      </button>}
    />
  );
}


function DocumentBar({ document, isDraft, onChanged, onNotice }) {
  const [busy, setBusy] = useState(false);
  async function draft() {
    setBusy(true);
    try {
      await adminApi(`/theory-documents/${document.id}/draft`, { method: "POST" });
      await onChanged();
      onNotice("Черновик создан");
    } finally {
      setBusy(false);
    }
  }
  async function publish() {
    if (!window.confirm("Опубликовать эту версию? Она сразу появится у пользователей.")) return;
    setBusy(true);
    try {
      await adminApi(`/theory-documents/${document.id}/publish`, { method: "POST" });
      await onChanged();
      onNotice("Новая версия опубликована");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="document-bar">
      <div>
        <span className={`status-dot ${isDraft ? "draft" : "published"}`} />
        <strong>
          Версия {document.editingVersion?.number || "—"} · {isDraft ? "черновик" : "опубликована"}
        </strong>
      </div>
      {isDraft ? (
        <button className="publish-action" disabled={busy} onClick={publish}>Опубликовать</button>
      ) : (
        <button className="primary-action small" disabled={busy} onClick={draft}>Редактировать</button>
      )}
    </div>
  );
}


function buildTree(blocks) {
  const nodes = new Map(blocks.map((block) => [block.id, { ...block, children: [] }]));
  const roots = [];
  nodes.forEach((node) => {
    const parent = nodes.get(node.parentId);
    if (parent && parent.id !== node.id) parent.children.push(node);
    else roots.push(node);
  });
  const sort = (items) => {
    items.sort((a, b) => a.sortOrder - b.sortOrder || a.id - b.id);
    items.forEach((item) => sort(item.children));
  };
  sort(roots);
  return roots;
}


function BlockTree({ blocks, selectedId, onSelect, disabled, documentId, onChanged }) {
  const tree = useMemo(() => buildTree(blocks), [blocks]);

  async function add(parentId = null) {
    const siblings = blocks.filter((block) => block.parentId === parentId);
    const sortOrder = siblings.length
      ? Math.max(...siblings.map((block) => block.sortOrder)) + 1
      : 0;
    const block = await adminApi(`/theory-documents/${documentId}/blocks`, {
      method: "POST",
      body: JSON.stringify({
        block_type: "rich_text",
        parent_block_id: parentId,
        data: { markdown: "" },
        settings: {},
        sort_order: sortOrder,
      }),
    });
    await onChanged(block.id);
  }

  return (
    <div className="block-tree-wrap">
      <div className="block-tree-heading">
        <h3>Структура документа</h3>
        <button className="primary-action small" onClick={() => add()} disabled={disabled}>+ Блок</button>
      </div>
      {!tree.length && <div className="empty-tree">Пока нет блоков</div>}
      <div className="block-tree">
        {tree.map((node) => (
          <BlockNode
            key={node.id}
            node={node}
            depth={0}
            selectedId={selectedId}
            onSelect={onSelect}
            onAdd={add}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}


function BlockNode({ node, depth, selectedId, onSelect, onAdd, disabled }) {
  return (
    <div className="block-node">
      <div className={node.id === selectedId ? "block-row active" : "block-row"} style={{ "--depth": depth }}>
        <button onClick={() => onSelect(node.id)}>
          <span className={`block-type-icon type-${node.type}`}>{blockSymbol(node.type)}</span>
          <span>
            <strong>{blockLabel(node.type)}</strong>
            <small>{blockExcerpt(node)}</small>
          </span>
        </button>
        <button className="inline-add" title="Добавить внутрь" disabled={disabled} onClick={() => onAdd(node.id)}>+</button>
      </div>
      {node.children.map((child) => (
        <BlockNode
          key={child.id}
          node={child}
          depth={depth + 1}
          selectedId={selectedId}
          onSelect={onSelect}
          onAdd={onAdd}
          disabled={disabled}
        />
      ))}
    </div>
  );
}


function blockLabel(type) {
  return BLOCK_TYPES.find(([value]) => value === type)?.[1] || type;
}

function blockSymbol(type) {
  return {
    rich_text: "¶",
    section: "▤",
    callout: "!",
    example: "→",
    list: "≡",
    table: "▦",
    image: "◇",
    video_embed: "▶",
  }[type] || "•";
}

function blockExcerpt(block) {
  const value = block.data?.markdown || block.data?.title || block.data?.url || "";
  return String(value).replace(/\s+/g, " ").slice(0, 54) || "Пустой блок";
}


function defaultData(type) {
  if (type === "section") return { title: "Новая подгруппа" };
  if (type === "list") return { style: "unordered", items: ["Новый пункт"] };
  if (type === "table") return { rows: [{ cells: ["Ячейка"] }] };
  if (type === "image") return { url: "", alt: "", caption: "" };
  if (type === "video_embed") return { url: "" };
  if (type === "callout") return { markdown: "", variant: "note" };
  return { markdown: "" };
}


function BlockEditor({ block, blocks, disabled, onSaved }) {
  const [draft, setDraft] = useState({
    type: block.type,
    parentId: block.parentId,
    data: block.data || {},
    settings: block.settings || {},
    sortOrder: block.sortOrder,
  });
  const [advanced, setAdvanced] = useState(false);
  const [dataJson, setDataJson] = useState(JSON.stringify(block.data || {}, null, 2));
  const [jsonError, setJsonError] = useState("");
  const [busy, setBusy] = useState(false);

  const siblings = blocks
    .filter((item) => item.parentId === block.parentId)
    .sort((a, b) => a.sortOrder - b.sortOrder || a.id - b.id);

  function changeType(type) {
    const data = defaultData(type);
    setDraft((current) => ({ ...current, type, data }));
    setDataJson(JSON.stringify(data, null, 2));
  }

  function updateData(patch) {
    const data = { ...draft.data, ...patch };
    setDraft((current) => ({ ...current, data }));
    setDataJson(JSON.stringify(data, null, 2));
  }

  async function save() {
    let data = draft.data;
    if (advanced) {
      try {
        data = JSON.parse(dataJson);
        setJsonError("");
      } catch {
        setJsonError("JSON содержит ошибку");
        return;
      }
    }
    setBusy(true);
    try {
      await adminApi(`/blocks/${block.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          block_type: draft.type,
          parent_block_id: draft.parentId,
          data,
          settings: draft.settings,
          sort_order: draft.sortOrder,
        }),
      });
      await onSaved();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm("Удалить блок вместе со всеми вложенными блоками?")) return;
    await adminApi(`/blocks/${block.id}`, { method: "DELETE" });
    await onSaved();
  }

  async function move(direction) {
    const index = siblings.findIndex((item) => item.id === block.id);
    const other = siblings[index + direction];
    if (!other) return;
    await Promise.all([
      adminApi(`/blocks/${block.id}`, {
        method: "PATCH",
        body: JSON.stringify({ sort_order: other.sortOrder }),
      }),
      adminApi(`/blocks/${other.id}`, {
        method: "PATCH",
        body: JSON.stringify({ sort_order: block.sortOrder }),
      }),
    ]);
    await onSaved();
  }

  return (
    <div className="block-editor">
      <div className="panel-heading">
        <div><p className="kicker">Блок #{block.id}</p><h2>Редактор</h2></div>
        <div className="move-actions">
          <button onClick={() => move(-1)} disabled={disabled}>↑</button>
          <button onClick={() => move(1)} disabled={disabled}>↓</button>
        </div>
      </div>
      {disabled && <div className="readonly-note">Создайте черновик, чтобы редактировать блоки.</div>}
      <label>Тип блока</label>
      <select value={draft.type} disabled={disabled} onChange={(event) => changeType(event.target.value)}>
        {BLOCK_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>

      <label>Родитель</label>
      <select
        value={draft.parentId || ""}
        disabled={disabled}
        onChange={(event) => setDraft((current) => ({
          ...current,
          parentId: event.target.value ? Number(event.target.value) : null,
        }))}
      >
        <option value="">Корень документа</option>
        {blocks.filter((item) => item.id !== block.id).map((item) => (
          <option key={item.id} value={item.id}>#{item.id} · {blockLabel(item.type)} · {blockExcerpt(item)}</option>
        ))}
      </select>

      <BlockFields draft={draft} disabled={disabled} updateData={updateData} />

      <button className="advanced-toggle" onClick={() => setAdvanced((value) => !value)}>
        {advanced ? "Скрыть JSON" : "Расширенные данные JSON"}
      </button>
      {advanced && (
        <>
          <textarea
            className="json-editor"
            value={dataJson}
            disabled={disabled}
            spellCheck={false}
            onChange={(event) => setDataJson(event.target.value)}
          />
          {jsonError && <div className="form-error">{jsonError}</div>}
        </>
      )}

      <div className="editor-actions">
        <button className="primary-action" onClick={save} disabled={disabled || busy}>
          {busy ? "Сохраняем…" : "Сохранить блок"}
        </button>
        <button className="danger-action" onClick={remove} disabled={disabled}>Удалить</button>
      </div>
    </div>
  );
}


function BlockFields({ draft, disabled, updateData }) {
  if (["rich_text", "example", "callout"].includes(draft.type)) {
    return (
      <>
        {draft.type === "callout" && (
          <>
            <label>Вариант</label>
            <select
              value={draft.data.variant || "note"}
              disabled={disabled}
              onChange={(event) => updateData({ variant: event.target.value })}
            >
              {CALLOUT_VARIANTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </>
        )}
        <label>Текст · Markdown</label>
        <textarea
          className="content-editor"
          value={draft.data.markdown || ""}
          disabled={disabled}
          placeholder="Введите текст…"
          onChange={(event) => updateData({ markdown: event.target.value })}
        />
      </>
    );
  }
  if (draft.type === "section") {
    return (
      <>
        <label>Название подгруппы</label>
        <input
          value={draft.data.title || ""}
          disabled={disabled}
          onChange={(event) => updateData({ title: event.target.value })}
        />
      </>
    );
  }
  if (draft.type === "image") {
    return (
      <>
        <label>URL изображения</label>
        <input value={draft.data.url || ""} disabled={disabled} onChange={(event) => updateData({ url: event.target.value })} />
        <label>Описание для доступности</label>
        <input value={draft.data.alt || ""} disabled={disabled} onChange={(event) => updateData({ alt: event.target.value })} />
        <label>Подпись</label>
        <input value={draft.data.caption || ""} disabled={disabled} onChange={(event) => updateData({ caption: event.target.value })} />
      </>
    );
  }
  if (draft.type === "video_embed") {
    return (
      <>
        <label>Ссылка на видео</label>
        <input value={draft.data.url || ""} disabled={disabled} onChange={(event) => updateData({ url: event.target.value })} />
      </>
    );
  }
  return (
    <div className="structured-hint">
      Данные списка или таблицы редактируются в JSON. В следующей версии добавим визуальный конструктор строк.
    </div>
  );
}


function PanelLoading() {
  return <div className="panel-loading"><span className="admin-loader" />Загрузка…</div>;
}

function EmptyPanel({ title, text, action = null, compact = false }) {
  return (
    <div className={compact ? "empty-panel compact" : "empty-panel"}>
      <span>◇</span>
      <h2>{title}</h2>
      <p>{text}</p>
      {action}
    </div>
  );
}
