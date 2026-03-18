import React, { useState, useRef, useEffect, useCallback } from "react";

export default function GroupsTab({ groups, tasks, onReload, registerAutoSave }) {
  const [selectedId, setSelectedId] = useState(null);
  const [nameDraft,  setNameDraft]  = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const dirtyRef = useRef(false);
  const snapRef  = useRef({});
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

  // Задания текущей выбранной группы
  const groupTasks = selectedId
    ? (tasks ?? []).filter(t => t.task_group_id === selectedId)
    : [];

  return (
    <div className="form-main">
      {/* LEFT */}
      <div className="form-tree">
        <div className="form-tree__header">Группы заданий</div>
        <div className="form-tree__scroll">
          {groups.map(g => {
            const count = (tasks ?? []).filter(t => t.task_group_id === g.id).length;
            return (
              <div
                key={g.id}
                className={selectedId === g.id
                  ? "form-tree__item form-tree__item--active"
                  : "form-tree__item"}
                onClick={() => handleSelect(g.id)}
              >
                <span className="form-tree__content">{g.name}</span>
                <span style={{ opacity: 0.4, fontSize: "0.78em", marginLeft: 6 }}>
                  ({count} зад.)
                </span>
              </div>
            );
          })}
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

            {/* ── Задания группы ── */}
            {selectedId && (
              <div style={{ marginTop: 18 }}>
                <div style={{
                  fontSize: "0.82rem", fontWeight: 600,
                  opacity: 0.65, marginBottom: 8,
                }}>
                  Задания группы ({groupTasks.length})
                </div>

                {groupTasks.length === 0 ? (
                  <div style={{ fontSize: "0.8rem", opacity: 0.4 }}>
                    В этой группе нет заданий
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    {groupTasks.map(t => (
                      <div
                        key={t.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "5px 10px",
                          borderRadius: 6,
                          background: "rgba(255,255,255,0.04)",
                          border: "1px solid rgba(255,255,255,0.07)",
                          fontSize: "0.82rem",
                        }}
                      >
                        <span>{t.name}</span>
                        <span style={{
                          display: "flex", gap: 8,
                          opacity: 0.45, fontSize: "0.78em",
                        }}>
                          <span>{TRAINER_TYPE_LABELS[t.trainer_type] ?? t.trainer_type ?? "—"}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Лейблы типов тренажёра — дублируем константу локально,
// чтобы GroupsTab не зависел от TasksTab
const TRAINER_TYPE_LABELS = {
  options:    "Опции",
  stress:     "Ударения",
  dictionary: "Словарные",
  input:      "Свободный ввод",
};
