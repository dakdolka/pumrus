import React, { useState, useRef, useEffect, useCallback } from "react";

const PARSERS = [
  { value: "caps",      label: "Caps — заглавная → пропуск" },
  { value: "custom_4",  label: "Custom4 — заглавная → строчная" },
  { value: "custom_14", label: "Слитно / Раздельно / Дефис" },
];

const EMPTY_MANUAL = {
  content_raw: "", content_visible: "", content_correct: "",
  correct_option_id: "", option_set_override_id: "",
  notice_wrong: "", notice_right: "",
};

export default function TaskItemsTab({
  taskId, options, optionSets, defaultOptionSetId, registerAutoSave,
}) {
  const [mode,          setMode]          = useState("bulk");
  const [items,         setItems]         = useState([]);
  const [parserType,    setParserType]    = useState("caps");
  const [bulkSetId,     setBulkSetId]     = useState(defaultOptionSetId ? String(defaultOptionSetId) : "");
  const [rawText,       setRawText]       = useState("");
  const [parsedItems,   setParsedItems]   = useState([]);
  const [parseError,    setParseError]    = useState("");
  const [isSavingBulk,  setIsSavingBulk]  = useState(false);
  const [manualDraft,   setManualDraft]   = useState(EMPTY_MANUAL);
  const [editingItemId, setEditingItemId] = useState(null);

  const dirtyRef = useRef(false);
  const snapRef  = useRef({});
  useEffect(() => {
    snapRef.current = { manualDraft, editingItemId };
  });

  const loadItems = useCallback(() =>
    fetch(`/api/tasks/general/${taskId}`)
      .then(r => r.json())
      .then(data => setItems(data.items ?? []))
      .catch(console.error), [taskId]);

  useEffect(() => {
    loadItems();
    setParsedItems([]); setRawText(""); setParseError("");
    setManualDraft(EMPTY_MANUAL); setEditingItemId(null);
    dirtyRef.current = false;
  }, [taskId]);

  // autoSave — только для ручного черновика
  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    const { manualDraft, editingItemId } = snapRef.current;
    if (!manualDraft.content_raw.trim()) { dirtyRef.current = false; return; }
    dirtyRef.current = false;

    const body = {
      content_raw:            manualDraft.content_raw.trim(),
      content_visible:        manualDraft.content_visible.trim(),
      content_correct:        manualDraft.content_correct.trim(),
      correct_option_id:      manualDraft.correct_option_id      ? Number(manualDraft.correct_option_id)      : null,
      option_set_override_id: manualDraft.option_set_override_id ? Number(manualDraft.option_set_override_id) : null,
      notice_wrong:           manualDraft.notice_wrong  || null,
      notice_right:           manualDraft.notice_right  || null,
    };

    if (editingItemId) {
      await fetch(`/api/tasks/general/items/${editingItemId}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } else {
      await fetch(`/api/tasks/general/${taskId}/items`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setManualDraft(EMPTY_MANUAL);
      setEditingItemId(null);
    }
    await loadItems();
  }, [taskId, loadItems]);

  useEffect(() => { registerAutoSave(autoSave); });

  // ── bulk ───────────────────────────────────────────────────────────────────
  const handleParse = async () => {
    setParseError("");
    let rawContent;
    try {
      const fixed = rawText.replace(/([{,]\s*)(\w+)\s*:/g, '$1"$2":');
      rawContent = JSON.parse(fixed);
    } catch {
      setParseError("Некорректный JSON");
      return;
    }

    // Формат {word, correct} — обрабатываем на фронте, не идём на бэкенд
    if (Array.isArray(rawContent) && rawContent[0]?.word !== undefined) {
      setParsedItems(rawContent.map(it => ({
        content_raw:       String(it.word),
        content_visible:   String(it.word),
        content_correct:   String(it.correct),
        correct_option_id: options.find(
          o => o.content.trim().toLowerCase() === String(it.correct).trim().toLowerCase()
        )?.id ?? null,
        notice_wrong: "",
        notice_right: "",
      })));
      return;
    }

    // Стандартный путь через бэкенд
    const res = await fetch("/api/tasks/general/parse-raw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        parser_type:   parserType,
        raw_items:     rawContent,
        option_set_id: bulkSetId ? Number(bulkSetId) : null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setParseError(err.detail || `Ошибка ${res.status}`);
      return;
    }
    const data = await res.json();
    setParsedItems(data.map(it => ({ ...it, notice_wrong: "", notice_right: "" })));
  };


  const handleSaveBulk = async () => {
    if (!parsedItems.length) return;
    setIsSavingBulk(true);
    try {
      await fetch(`/api/tasks/general/${taskId}/items/bulk`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsedItems.map(it => ({
          content_raw:            it.content_raw,
          content_visible:        it.content_visible,
          content_correct:        it.content_correct,
          correct_option_id:      it.correct_option_id      || null,
          option_set_override_id: null,
          notice_wrong:           it.notice_wrong            || null,
          notice_right:           it.notice_right            || null,
        }))),
      });
      setParsedItems([]); setRawText("");
      await loadItems();
    } finally { setIsSavingBulk(false); }
  };

  const updateParsed = (idx, field, value) =>
    setParsedItems(prev => prev.map((it, i) => i === idx ? { ...it, [field]: value } : it));

  // ── manual ─────────────────────────────────────────────────────────────────
  const handleEditItem = async (item) => {
    await autoSave();
    setEditingItemId(item.id);
    setManualDraft({
      content_raw:            item.content_raw            ?? "",
      content_visible:        item.content_visible        ?? "",
      content_correct:        item.content_correct        ?? "",
      correct_option_id:      item.correct_option_id      ? String(item.correct_option_id)      : "",
      option_set_override_id: item.option_set_override_id ? String(item.option_set_override_id) : "",
      notice_wrong:           item.notice_wrong           ?? "",
      notice_right:           item.notice_right           ?? "",
    });
    setMode("manual");
    dirtyRef.current = false;
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setManualDraft(EMPTY_MANUAL);
    dirtyRef.current = false;
  };

  const handleDeleteItem = async (id) => {
    if (!window.confirm("Удалить элемент?")) return;
    if (editingItemId === id) handleCancelEdit();
    await fetch(`/api/tasks/general/items/${id}`, { method: "DELETE" });
    await loadItems();
  };

  const setField = (field) => (e) => {
    setManualDraft(prev => ({ ...prev, [field]: e.target.value }));
    dirtyRef.current = true;
  };

  // ── стили ──────────────────────────────────────────────────────────────────
  const inlineInput  = { fontSize: "0.78rem", background: "transparent", color: "var(--text-color)", border: "1px solid rgba(255,255,255,0.18)", borderRadius: 4, padding: "2px 4px", width: "100%" };
  const inlineSelect = { ...inlineInput, background: "var(--block-color)", cursor: "pointer" };
  const deleteBtn    = { padding: "2px 7px", borderRadius: 4, border: "none", background: "#b00020", color: "#fff", cursor: "pointer", fontSize: "0.75rem" };
  const editBtn      = { ...deleteBtn, background: "rgba(255,255,255,0.12)", marginRight: 4 };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, overflow: "hidden" }}>

      {/* ── mode tabs ── */}
      <div className="form-tabs" style={{ marginBottom: 8 }}>
        {[{ key: "bulk", label: "Bulk-парсинг" }, { key: "manual", label: "Вручную" }].map(t => (
          <button
            key={t.key}
            className={mode === t.key ? "form-tab form-tab--active" : "form-tab"}
            onClick={() => setMode(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── верхняя часть: режим ── */}
      <div style={{ flex: "0 0 auto" }}>

        {/* BULK */}
        {mode === "bulk" && (
          <div>
            <div className="form-editor__field">
              <label>Парсер</label>
              <select value={parserType} onChange={e => { setParserType(e.target.value); setParsedItems([]); setParseError(""); }}>
                {PARSERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div className="form-editor__field">
              <label>Набор опций</label>
              <select value={bulkSetId} onChange={e => setBulkSetId(e.target.value)}>
                <option value="">Без автоматчинга</option>
                {optionSets.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-editor__field" style={{ flexDirection: "column", alignItems: "stretch" }}>
              <label style={{ marginBottom: 4 }}>Raw-массив (JSON)</label>
              <textarea
                value={rawText} rows={4}
                onChange={e => { setRawText(e.target.value); setParsedItems([]); setParseError(""); }}
                placeholder='["прИбой", "катАлог"]'
              />
            </div>
            {parseError && (
              <div style={{ color: "#ff6b6b", fontSize: "0.83rem", marginBottom: 6 }}>{parseError}</div>
            )}
            <div className="form-editor__actions">
              <button onClick={handleParse}>Сгенерировать</button>
              {parsedItems.length > 0 && (
                <button onClick={handleSaveBulk} disabled={isSavingBulk}>
                  {isSavingBulk ? "Сохраняем…" : `Сохранить ${parsedItems.length} эл.`}
                </button>
              )}
            </div>

            {/* предпросмотр */}
            {parsedItems.length > 0 && (
              <div style={{ overflowX: "auto", marginTop: 8, marginBottom: 12 }}>
                <table style={{ width: "100%", fontSize: "0.78rem", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ opacity: 0.55 }}>
                      {["#","raw","visible","correct","option","notice ✗","notice ✓"].map(h => (
                        <th key={h} style={{ textAlign: "left", padding: "3px 5px", whiteSpace: "nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsedItems.map((it, idx) => (
                      <tr key={idx} style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}>
                        <td style={{ padding: "3px 5px", opacity: 0.45 }}>{idx + 1}</td>
                        <td style={{ padding: "3px 5px" }}>{it.content_raw}</td>
                        <td style={{ padding: "3px 5px" }}>{it.content_visible}</td>
                        <td style={{ padding: "3px 5px", fontWeight: 600 }}>{it.content_correct}</td>
                        <td style={{ padding: "3px 5px" }}>
                          <select value={it.correct_option_id ?? ""} onChange={e => updateParsed(idx, "correct_option_id", e.target.value ? Number(e.target.value) : null)} style={inlineSelect}>
                            <option value="">—</option>
                            {options.map(o => <option key={o.id} value={o.id}>{o.content}</option>)}
                          </select>
                        </td>
                        <td style={{ padding: "3px 5px" }}>
                          <input type="text" value={it.notice_wrong} onChange={e => updateParsed(idx, "notice_wrong", e.target.value)} placeholder="подсказка" style={inlineInput} />
                        </td>
                        <td style={{ padding: "3px 5px" }}>
                          <input type="text" value={it.notice_right} onChange={e => updateParsed(idx, "notice_right", e.target.value)} placeholder="подсказка" style={inlineInput} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* MANUAL — форма */}
        {mode === "manual" && (
          <div style={{
            background: "rgba(255,255,255,0.03)",
            borderRadius: 8, padding: "10px 8px", marginBottom: 10,
            border: editingItemId ? "1px solid var(--active-color)" : "1px solid rgba(255,255,255,0.08)",
          }}>
            <div style={{ fontSize: "0.82rem", opacity: 0.6, marginBottom: 8 }}>
              {editingItemId ? `Редактирование #${editingItemId}` : "Новый элемент"}
            </div>
            {[
              { key: "content_raw",     label: "Raw" },
              { key: "content_visible", label: "Visible" },
              { key: "content_correct", label: "Correct" },
              { key: "notice_wrong",    label: "Notice ✗" },
              { key: "notice_right",    label: "Notice ✓" },
            ].map(({ key, label }) => (
              <div className="form-editor__field" key={key} style={{ marginBottom: 5 }}>
                <label style={{ minWidth: 80 }}>{label}</label>
                <input type="text" value={manualDraft[key]} onChange={setField(key)} />
              </div>
            ))}
            <div className="form-editor__field" style={{ marginBottom: 5 }}>
              <label style={{ minWidth: 80 }}>Опция</label>
              <select value={manualDraft.correct_option_id} onChange={setField("correct_option_id")}>
                <option value="">Не выбрана</option>
                {options.map(o => <option key={o.id} value={o.id}>{o.content}</option>)}
              </select>
            </div>
            <div className="form-editor__field" style={{ marginBottom: 5 }}>
              <label style={{ minWidth: 80 }}>Набор</label>
              <select value={manualDraft.option_set_override_id} onChange={setField("option_set_override_id")}>
                <option value="">Не выбран</option>
                {optionSets.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-editor__actions">
              <button onClick={autoSave}>
                {editingItemId ? "Сохранить изменения" : "Добавить элемент"}
              </button>
              {editingItemId && (
                <button onClick={handleCancelEdit} style={{ background: "rgba(255,255,255,0.1)" }}>
                  Отмена
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── НИЗ: существующие элементы — всегда видны ── */}
      <div style={{ flex: "1 1 auto", minHeight: 0, overflowY: "auto", marginTop: 8 }}>
        {items.length === 0 ? (
          <div style={{ opacity: 0.4, fontSize: "0.82rem" }}>Элементов пока нет</div>
        ) : (
          <>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, marginBottom: 6, opacity: 0.7 }}>
              Элементы задания ({items.length})
            </div>
            <table style={{ width: "100%", fontSize: "0.78rem", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ opacity: 0.55 }}>
                  {["#","raw","visible","correct","опция","notice ✗","notice ✓",""].map((h, i) => (
                    <th key={i} style={{ textAlign: "left", padding: "3px 5px", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((it, idx) => (
                  <tr
                    key={it.id}
                    style={{
                      borderTop: "1px solid rgba(255,255,255,0.07)",
                      background: editingItemId === it.id ? "rgba(255,255,255,0.05)" : "transparent",
                    }}
                  >
                    <td style={{ padding: "3px 5px", opacity: 0.45 }}>{idx + 1}</td>
                    <td style={{ padding: "3px 5px" }}>{it.content_raw}</td>
                    <td style={{ padding: "3px 5px" }}>{it.content_visible}</td>
                    <td style={{ padding: "3px 5px", fontWeight: 600 }}>{it.content_correct}</td>
                    <td style={{ padding: "3px 5px", opacity: 0.65 }}>{it.correct_option?.content ?? "—"}</td>
                    <td style={{ padding: "3px 5px", opacity: 0.55 }}>{it.notice_wrong ?? "—"}</td>
                    <td style={{ padding: "3px 5px", opacity: 0.55 }}>{it.notice_right ?? "—"}</td>
                    <td style={{ padding: "3px 5px", whiteSpace: "nowrap" }}>
                      <button style={editBtn} onClick={() => handleEditItem(it)}>✎</button>
                      <button style={deleteBtn} onClick={() => handleDeleteItem(it.id)}>✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
