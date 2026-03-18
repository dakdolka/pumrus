import React, { useState, useRef, useEffect, useCallback } from "react";
import TaskItemsTab from "./TaskItemsTab";

export const TRAINER_TYPES = [
  { value: "options",    label: "Опции (выбор варианта)" },
  { value: "stress",     label: "Ударения (клик по гласной)" },
  { value: "dictionary", label: "Словарные слова (пропуски)" },
  { value: "input",      label: "Свободный ввод текста" },
];

export default function TasksTab({
  groups, options, optionSets,
  tasks, onTasksReload,          // ← из TasksAdmin
  registerAutoSave,
}) {
  const [selectedTaskId,  setSelectedTaskId]  = useState(null);
  const [innerTab,        setInnerTab]        = useState("meta");
  const [expandedGroups,  setExpandedGroups]  = useState([]);
  const [isCreating,      setIsCreating]      = useState(false);

  // meta draft
  const [nameDraft,         setNameDraft]         = useState("");
  const [groupIdDraft,      setGroupIdDraft]       = useState("");
  const [optionSetIdDraft,  setOptionSetIdDraft]   = useState("");
  const [trainerTypeDraft,  setTrainerTypeDraft]   = useState("options"); // ← новое

  const dirtyRef     = useRef(false);
  const snapRef      = useRef({});
  const innerSaveRef = useRef(null);

  useEffect(() => {
    snapRef.current = {
      selectedTaskId, nameDraft, groupIdDraft,
      optionSetIdDraft, trainerTypeDraft, isCreating,
    };
  });

  // ── save meta ──────────────────────────────────────────
  const doSave = useCallback(async (snap) => {
    const {
      selectedTaskId, nameDraft, groupIdDraft,
      optionSetIdDraft, trainerTypeDraft, isCreating,
    } = snap;
    if (!nameDraft.trim()) return null;

    const body = {
      name:                  nameDraft.trim(),
      task_group_id:         groupIdDraft       ? Number(groupIdDraft)       : null,
      default_option_set_id: optionSetIdDraft   ? Number(optionSetIdDraft)   : null,
      trainer_type:          trainerTypeDraft   || "options",
    };

    if (isCreating) {
      const created = await fetch("/api/tasks/general/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(r => r.json());
      setIsCreating(false);
      setSelectedTaskId(created.id);
      await onTasksReload();
      return created.id;
    } else if (selectedTaskId) {
      await fetch(`/api/tasks/general/${selectedTaskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await onTasksReload();
      return selectedTaskId;
    }
    return null;
  }, [onTasksReload]);

  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    dirtyRef.current = false;
    await doSave(snapRef.current);
  }, [doSave]);

  useEffect(() => { registerAutoSave(autoSave); });

  // ── inner tab switch ───────────────────────────────────
  const handleInnerTabSwitch = async (tab) => {
    if (tab === innerTab) return;
    await autoSave();
    if (innerSaveRef.current) await innerSaveRef.current();
    setInnerTab(tab);
  };

  // ── apply task ─────────────────────────────────────────
  const applyTask = (task) => {
    setSelectedTaskId(task.id);
    setIsCreating(false);
    setNameDraft(task.name ?? "");
    setGroupIdDraft(
      task.task_group_id    ? String(task.task_group_id)
      : task.task_group?.id ? String(task.task_group.id)
      : ""
    );
    setOptionSetIdDraft(
      task.default_option_set_id    ? String(task.default_option_set_id)
      : task.default_option_set?.id ? String(task.default_option_set.id)
      : ""
    );
    setTrainerTypeDraft(task.trainer_type ?? "options");
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
    setTrainerTypeDraft("options");
    setInnerTab("meta");
    dirtyRef.current = false;
  };

  const handleDelete = async () => {
    if (!selectedTaskId || !window.confirm("Удалить задание?")) return;
    await fetch(`/api/tasks/general/${selectedTaskId}`, { method: "DELETE" });
    setSelectedTaskId(null);
    setNameDraft("");
    setTrainerTypeDraft("options");
    setIsCreating(false);
    dirtyRef.current = false;
    await onTasksReload();
  };

  const toggleGroup = (id) =>
    setExpandedGroups(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );

  // ── группировка ────────────────────────────────────────
  const tasksByGroup = groups.map(g => ({
    ...g,
    tasks: tasks.filter(t => t.task_group_id === g.id),
  }));
  const ungrouped = tasks.filter(t => !t.task_group_id);
  const isEditing  = !!selectedTaskId || isCreating;

  // Метка типа тренажёра для дерева
  const typeLabel = (t) => {
    const found = TRAINER_TYPES.find(x => x.value === t.trainer_type);
    return found ? found.label.split(" ")[0] : "—";
  };

  return (
    <div className="form-main">

      {/* ── LEFT ── */}
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
                    <span style={{ opacity: 0.35, fontSize: "0.75em", marginLeft: 6 }}>
                      {typeLabel(t)}
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
                  <span className="form-tree__content">{t.name}</span>
                  <span style={{ opacity: 0.35, fontSize: "0.75em", marginLeft: 6 }}>
                    {typeLabel(t)}
                  </span>
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

      {/* ── RIGHT ── */}
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
                { key: "items", label: "Элементы" },
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
                  <label>Тип тренажёра</label>
                  <select
                    value={trainerTypeDraft}
                    onChange={e => { setTrainerTypeDraft(e.target.value); dirtyRef.current = true; }}
                  >
                    {TRAINER_TYPES.map(tt => (
                      <option key={tt.value} value={tt.value}>{tt.label}</option>
                    ))}
                  </select>
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

                {/* Набор опций только для опционных тренажёров */}
                {(trainerTypeDraft === "options" || trainerTypeDraft === "dictionary") && (
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
                )}

                {/* Подсказка под полем */}
                <div style={{
                  fontSize: "0.78rem", opacity: 0.45,
                  marginBottom: 12, marginTop: -4,
                }}>
                  {trainerTypeDraft === "stress"
                    ? "Ударения: content_visible = слово строчными, content_correct = слово с заглавной ударной буквой"
                    : trainerTypeDraft === "dictionary"
                    ? "Словарные: content_visible = слово с _ на месте пропусков, content_correct = полное слово"
                    : trainerTypeDraft === "input"
                    ? "Свободный ввод: ответ сравнивается с content_correct без учёта регистра"
                    : "Опции: правильный ответ задаётся через correct_option или набор опций"}
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
                trainerType={trainerTypeDraft}             // ← передаём тип
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
