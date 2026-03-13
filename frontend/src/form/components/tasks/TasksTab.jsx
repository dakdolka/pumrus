import React, { useState, useRef, useEffect, useCallback } from "react";
import TaskItemsTab from "./TaskItemsTab";

export default function TasksTab({ groups, options, optionSets, registerAutoSave }) {
  const [tasks,           setTasks]           = useState([]);
  const [selectedTaskId,  setSelectedTaskId]  = useState(null);
  const [innerTab,        setInnerTab]        = useState("meta");
  const [expandedGroups,  setExpandedGroups]  = useState([]);
  const [isCreating,      setIsCreating]      = useState(false);

  // meta draft
  const [nameDraft,        setNameDraft]        = useState("");
  const [groupIdDraft,     setGroupIdDraft]     = useState("");
  const [optionSetIdDraft, setOptionSetIdDraft] = useState("");

  const dirtyRef    = useRef(false);
  const snapRef     = useRef({});
  const innerSaveRef = useRef(null); // TaskItemsTab's autoSave

  useEffect(() => {
    snapRef.current = { selectedTaskId, nameDraft, groupIdDraft, optionSetIdDraft, isCreating };
  });

  const loadTasks = useCallback(() =>
    fetch("/api/tasks/general/")
      .then(r => r.json()).then(setTasks).catch(console.error), []);

  useEffect(() => { loadTasks(); }, []);

  // ── save meta ──────────────────────────────────────────────────────────────
  const doSave = useCallback(async (snap) => {
    const { selectedTaskId, nameDraft, groupIdDraft, optionSetIdDraft, isCreating } = snap;
    if (!nameDraft.trim()) return null;

    const body = {
      name:                  nameDraft.trim(),
      task_group_id:         groupIdDraft        ? Number(groupIdDraft)     : null,
      default_option_set_id: optionSetIdDraft    ? Number(optionSetIdDraft) : null,
    };

    if (isCreating) {
      const created = await fetch("/api/tasks/general/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(r => r.json());
      setIsCreating(false);
      setSelectedTaskId(created.id);
      await loadTasks();
      return created.id;
    } else if (selectedTaskId) {
      await fetch(`/api/tasks/general/${selectedTaskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await loadTasks();
      return selectedTaskId;
    }
    return null;
  }, [loadTasks]);

  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    dirtyRef.current = false;
    await doSave(snapRef.current);
  }, [doSave]);

  useEffect(() => { registerAutoSave(autoSave); });

  // ── inner tab switch ───────────────────────────────────────────────────────
  const handleInnerTabSwitch = async (tab) => {
    if (tab === innerTab) return;
    await autoSave(); // сохраняем мету
    if (innerSaveRef.current) await innerSaveRef.current();
    setInnerTab(tab);
  };

  // ── select task ────────────────────────────────────────────────────────────
  const applyTask = (task) => {
    setSelectedTaskId(task.id);
    setIsCreating(false);
    setNameDraft(task.name ?? "");
    setGroupIdDraft(task.task_group_id ? String(task.task_group_id) : "");
    setOptionSetIdDraft(task.default_option_set_id ? String(task.default_option_set_id) : "");
    dirtyRef.current = false;
  };

  const handleSelectTask = async (id) => {
    await autoSave();
    if (innerSaveRef.current) await innerSaveRef.current();
    const task = tasks.find(t => t.id === id);
    if (task) applyTask(task);
    setInnerTab("meta");
  };

  const handleStartCreate = async () => {
    await autoSave();
    if (innerSaveRef.current) await innerSaveRef.current();
    setSelectedTaskId(null);
    setIsCreating(true);
    setNameDraft("");
    setGroupIdDraft(groups[0] ? String(groups[0].id) : "");
    setOptionSetIdDraft("");
    setInnerTab("meta");
    dirtyRef.current = false;
  };

  const handleDelete = async () => {
    if (!selectedTaskId || !window.confirm("Удалить задание?")) return;
    await fetch(`/api/tasks/general/${selectedTaskId}`, { method: "DELETE" });
    setSelectedTaskId(null);
    setNameDraft("");
    setIsCreating(false);
    dirtyRef.current = false;
    await loadTasks();
  };

  const toggleGroup = (id) =>
    setExpandedGroups(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );

  // группируем задания
  const tasksByGroup = groups.map(g => ({
    ...g,
    tasks: tasks.filter(t => t.task_group_id === g.id),
  }));
  const ungrouped = tasks.filter(t => !t.task_group_id);
  const isEditing  = !!selectedTaskId || isCreating;

  return (
    <div className="form-main">
      {/* LEFT: список заданий */}
      <div className="form-tree">
        <div className="form-tree__header">Задания</div>
        <div className="form-tree__scroll">
          {tasksByGroup.map(g => {
            const expanded = expandedGroups.includes(g.id);
            return (
              <div key={g.id}>
                <div
                  className="form-tree__item"
                  style={{ fontWeight: 600 }}
                  onClick={() => toggleGroup(g.id)}
                >
                  <span style={{ marginRight: 6 }}>{expanded ? "▾" : "▸"}</span>
                  {g.name}
                  <span style={{ opacity: 0.4, fontSize: "0.78em", marginLeft: 6 }}>
                    ({g.tasks.length})
                  </span>
                </div>
                {expanded && g.tasks.map(t => (
                  <div
                    key={t.id}
                    className={selectedTaskId === t.id
                      ? "form-tree__item form-tree__item--active"
                      : "form-tree__item"}
                    style={{ paddingLeft: 24 }}
                    onClick={() => handleSelectTask(t.id)}
                  >
                    <span className="form-tree__content">{t.name}</span>
                    <span style={{ opacity: 0.4, fontSize: "0.78em", marginLeft: 6 }}>
                      ({(t.items ?? []).length})
                    </span>
                  </div>
                ))}
              </div>
            );
          })}

          {ungrouped.length > 0 && (
            <div>
              <div className="form-tree__item" style={{ opacity: 0.45, fontSize: "0.82em" }}>
                Без группы
              </div>
              {ungrouped.map(t => (
                <div
                  key={t.id}
                  className={selectedTaskId === t.id
                    ? "form-tree__item form-tree__item--active"
                    : "form-tree__item"}
                  style={{ paddingLeft: 16 }}
                  onClick={() => handleSelectTask(t.id)}
                >
                  {t.name}
                </div>
              ))}
            </div>
          )}

          {isCreating && (
            <div className="form-tree__item form-tree__item--active">
              <em>Новое задание…</em>
            </div>
          )}
        </div>
        <button className="form-tree__add" onClick={handleStartCreate}>
          + Добавить задание
        </button>
      </div>

      {/* RIGHT: редактор */}
      <div className="form-editor" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
        <div className="form-editor__header">
          {isCreating ? "Новое задание" : selectedTaskId ? "Редактор задания" : "Выберите задание"}
        </div>

        {isEditing && (
          <>
            {/* внутренние табы */}
            <div className="form-tabs" style={{ marginBottom: 10 }}>
              {[
                { key: "meta",  label: "Мета" },
                { key: "items", label: `Элементы` },
              ].map(t => (
                <button
                  key={t.key}
                  className={innerTab === t.key ? "form-tab form-tab--active" : "form-tab"}
                  onClick={() => handleInnerTabSwitch(t.key)}
                  disabled={t.key === "items" && isCreating}
                  title={t.key === "items" && isCreating ? "Сначала сохраните задание" : ""}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* ── МЕТА ── */}
            {innerTab === "meta" && (
              <div>
                <div className="form-editor__field">
                  <label>Название</label>
                  <input
                    type="text"
                    value={nameDraft}
                    onChange={e => { setNameDraft(e.target.value); dirtyRef.current = true; }}
                  />
                </div>

                <div className="form-editor__field">
                  <label>Группа</label>
                  <select
                    value={groupIdDraft}
                    onChange={e => { setGroupIdDraft(e.target.value); dirtyRef.current = true; }}
                  >
                    <option value="">Без группы</option>
                    {groups.map(g => (
                      <option key={g.id} value={g.id}>{g.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-editor__field">
                  <label>Набор опций</label>
                  <select
                    value={optionSetIdDraft}
                    onChange={e => { setOptionSetIdDraft(e.target.value); dirtyRef.current = true; }}
                  >
                    <option value="">Не задан</option>
                    {optionSets.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-editor__actions">
                  <button onClick={autoSave}>Сохранить</button>
                  {selectedTaskId && (
                    <button className="form-editor__delete" onClick={handleDelete}>
                      Удалить задание
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* ── ЭЛЕМЕНТЫ ── */}
            {innerTab === "items" && selectedTaskId && (
              <TaskItemsTab
                taskId={selectedTaskId}
                options={options}
                optionSets={optionSets}
                defaultOptionSetId={optionSetIdDraft ? Number(optionSetIdDraft) : null}
                registerAutoSave={(fn) => { innerSaveRef.current = fn; }}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
