import React, { useState, useRef, useEffect, useCallback } from "react";

export default function GroupsTab({ groups, onReload, registerAutoSave }) {
  const [selectedId, setSelectedId] = useState(null);
  const [nameDraft,  setNameDraft]  = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const dirtyRef = useRef(false);
  // всегда актуальный снимок стейта для autoSave
  const snapRef = useRef({});
  useEffect(() => {
    snapRef.current = { selectedId, nameDraft, isCreating };
  });

  const doSave = useCallback(async (snap) => {
    const { selectedId, nameDraft, isCreating } = snap;
    if (!nameDraft.trim()) return;

    if (isCreating) {
      await fetch("/api/tasks/general/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nameDraft.trim() }),
      });
      setIsCreating(false);
    } else if (selectedId) {
      await fetch(`/api/tasks/general/groups/${selectedId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nameDraft.trim() }),
      });
    }
    await onReload();
  }, [onReload]);

  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    dirtyRef.current = false;
    await doSave(snapRef.current);
  }, [doSave]);

  // регистрируем при каждом рендере — ref в parent всегда свежий
  useEffect(() => { registerAutoSave(autoSave); });

  const handleSelect = async (id) => {
    await autoSave();
    const g = groups.find(x => x.id === id);
    setSelectedId(id);
    setIsCreating(false);
    setNameDraft(g?.name ?? "");
    dirtyRef.current = false;
  };

  const handleStartCreate = async () => {
    await autoSave();
    setSelectedId(null);
    setIsCreating(true);
    setNameDraft("");
    dirtyRef.current = false;
  };

  const handleDelete = async () => {
    if (!selectedId || !window.confirm("Удалить группу?")) return;
    await fetch(`/api/tasks/general/groups/${selectedId}`, { method: "DELETE" });
    setSelectedId(null);
    setNameDraft("");
    dirtyRef.current = false;
    await onReload();
  };

  return (
    <div className="form-main">
      {/* LEFT */}
      <div className="form-tree">
        <div className="form-tree__header">Группы заданий</div>
        <div className="form-tree__scroll">
          {groups.map(g => (
            <div
              key={g.id}
              className={selectedId === g.id
                ? "form-tree__item form-tree__item--active"
                : "form-tree__item"}
              onClick={() => handleSelect(g.id)}
            >
              {g.name}
            </div>
          ))}
          {isCreating && (
            <div className="form-tree__item form-tree__item--active">
              <em>Новая группа…</em>
            </div>
          )}
        </div>
        <button className="form-tree__add" onClick={handleStartCreate}>
          + Добавить группу
        </button>
      </div>

      {/* RIGHT */}
      <div className="form-editor">
        <div className="form-editor__header">
          {isCreating ? "Новая группа" : selectedId ? "Редактор группы" : "Выберите группу"}
        </div>
        {(selectedId || isCreating) && (
          <>
            <div className="form-editor__field">
              <label>Название</label>
              <input
                type="text"
                value={nameDraft}
                onChange={e => { setNameDraft(e.target.value); dirtyRef.current = true; }}
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
