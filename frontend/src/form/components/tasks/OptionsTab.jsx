import React, { useState, useRef, useEffect, useCallback } from "react";

export default function OptionsTab({ options, onReload, registerAutoSave }) {
  const [selectedId,   setSelectedId]   = useState(null);
  const [contentDraft, setContentDraft] = useState("");
  const [extrasDraft,  setExtrasDraft]  = useState("");
  const [isCreating,   setIsCreating]   = useState(false);

  const dirtyRef = useRef(false);
  const snapRef  = useRef({});
  useEffect(() => {
    snapRef.current = { selectedId, contentDraft, extrasDraft, isCreating };
  });

  const doSave = useCallback(async (snap) => {
    const { selectedId, contentDraft, extrasDraft, isCreating } = snap;
    if (!contentDraft.trim()) return;

    const body = { content: contentDraft.trim(), extras: extrasDraft.trim() || null };

    if (isCreating) {
      await fetch("/api/tasks/general/options", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setIsCreating(false);
    } else if (selectedId) {
      await fetch(`/api/tasks/general/options/${selectedId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    await onReload();
  }, [onReload]);

  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    dirtyRef.current = false;
    await doSave(snapRef.current);
  }, [doSave]);

  useEffect(() => { registerAutoSave(autoSave); });

  const handleSelect = async (id) => {
    await autoSave();
    const o = options.find(x => x.id === id);
    setSelectedId(id);
    setIsCreating(false);
    setContentDraft(o?.content ?? "");
    setExtrasDraft(o?.extras ?? "");
    dirtyRef.current = false;
  };

  const handleStartCreate = async () => {
    await autoSave();
    setSelectedId(null);
    setIsCreating(true);
    setContentDraft("");
    setExtrasDraft("");
    dirtyRef.current = false;
  };

  const handleDelete = async () => {
    if (!selectedId || !window.confirm("Удалить опцию?")) return;
    await fetch(`/api/tasks/general/options/${selectedId}`, { method: "DELETE" });
    setSelectedId(null);
    setContentDraft("");
    setExtrasDraft("");
    dirtyRef.current = false;
    await onReload();
  };

  const mark = (setter) => (e) => {
    setter(e.target.value);
    dirtyRef.current = true;
  };

  return (
    <div className="form-main">
      {/* LEFT */}
      <div className="form-tree">
        <div className="form-tree__header">Опции</div>
        <div className="form-tree__scroll">
          {options.map(o => (
            <div
              key={o.id}
              className={selectedId === o.id
                ? "form-tree__item form-tree__item--active"
                : "form-tree__item"}
              onClick={() => handleSelect(o.id)}
            >
              <span style={{ opacity: 0.4, fontSize: "0.78em", marginRight: 6 }}>#{o.id}</span>
              <span className="form-tree__content">{o.content}</span>
              {o.extras && (
                <span style={{ opacity: 0.4, fontSize: "0.78em", marginLeft: 6 }}>
                  [{o.extras}]
                </span>
              )}
            </div>
          ))}
          {isCreating && (
            <div className="form-tree__item form-tree__item--active">
              <em>Новая опция…</em>
            </div>
          )}
        </div>
        <button className="form-tree__add" onClick={handleStartCreate}>
          + Добавить опцию
        </button>
      </div>

      {/* RIGHT */}
      <div className="form-editor">
        <div className="form-editor__header">
          {isCreating ? "Новая опция" : selectedId ? "Редактор опции" : "Выберите опцию"}
        </div>
        {(selectedId || isCreating) && (
          <>
            <div className="form-editor__field">
              <label>Контент</label>
              <input type="text" value={contentDraft} onChange={mark(setContentDraft)} />
            </div>
            <div className="form-editor__field">
              <label>Extras</label>
              <input
                type="text"
                value={extrasDraft}
                onChange={mark(setExtrasDraft)}
                placeholder="Необязательно"
              />
            </div>
            <div className="form-editor__actions">
              <button onClick={autoSave}>Сохранить</button>
              {selectedId && (
                <button className="form-editor__delete" onClick={handleDelete}>
                  Удалить
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
