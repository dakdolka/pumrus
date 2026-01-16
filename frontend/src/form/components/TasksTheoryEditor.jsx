import React, { useEffect, useState } from "react";

/**
 * props:
 * - subjectId: number
 * - theories: список теорий по предмету (из FormApp)
 */
export function TasksTheoryEditor({ subjectId, theories }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const [groupNameDraft, setGroupNameDraft] = useState("");
  const [groupIsSingleDraft, setGroupIsSingleDraft] = useState(false);

  const [taskNameDraft, setTaskNameDraft] = useState("");
  const [selectedTheoryIdsForTask, setSelectedTheoryIdsForTask] = useState([]);

  // какие группы раскрыты (только для is_single = false)
  const [expandedGroupIds, setExpandedGroupIds] = useState([]);

  // загрузка групп/тасков для предмета
  useEffect(() => {
    if (!subjectId) {
      setGroups([]);
      setSelectedGroupId(null);
      setSelectedTaskId(null);
      setExpandedGroupIds([]);
      return;
    }

    fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`)
      .then((r) => r.json())
      .then((data) => {
        const items = data || [];
        setGroups(items);

        const firstGroup = items[0] || null;
        const firstTask =
          firstGroup && firstGroup.tasks && firstGroup.tasks[0]
            ? firstGroup.tasks[0]
            : null;

        setSelectedGroupId(firstGroup ? firstGroup.task_group_id : null);
        setSelectedTaskId(firstTask ? firstTask.task_id : null);

        // все группы стартуют свёрнутыми
        setExpandedGroupIds([]);
      })
      .catch(console.error);
  }, [subjectId]);

  // когда выбрана группа – подставляем её данные в драфт
  useEffect(() => {
    const group = groups.find((g) => g.task_group_id === selectedGroupId);
    if (!group) {
      setGroupNameDraft("");
      setGroupIsSingleDraft(false);
      return;
    }

    setGroupNameDraft(group.group_name || "");
    setGroupIsSingleDraft(!!group.is_single);
  }, [selectedGroupId, groups]);

  // когда выбрана задача – подставляем её имя и привязанные теории
  useEffect(() => {
    let task = null;
    groups.forEach((g) => {
      const found = (g.tasks || []).find((t) => t.task_id === selectedTaskId);
      if (found) {
        task = found;
      }
    });

    if (!task) {
      setTaskNameDraft("");
      setSelectedTheoryIdsForTask([]);
      return;
    }

    setTaskNameDraft(task.task_name || "");

    const ids = (task.theories || []).map((th) => th.theory_id);
    setSelectedTheoryIdsForTask(ids);
  }, [selectedTaskId, groups]);

  // переключение раскрытия группы
  function toggleGroupExpanded(groupId) {
    setExpandedGroupIds((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  }

  // создание новой группы
  function handleCreateGroup() {
    const name = prompt("Название новой группы задач:");
    if (!name || !subjectId) return;

    fetch("/api/theory/task-groups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        is_single: false,
        subject_id: subjectId,
      }),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        const items = data || [];
        setGroups(items);

        const firstGroup = items[0] || null;
        const firstTask =
          firstGroup && firstGroup.tasks && firstGroup.tasks[0]
            ? firstGroup.tasks[0]
            : null;

        setSelectedGroupId(firstGroup ? firstGroup.task_group_id : null);
        setSelectedTaskId(firstTask ? firstTask.task_id : null);

        const expanded = items
          .filter((g) => !g.is_single)
          .map((g) => g.task_group_id);
        setExpandedGroupIds(expanded);
      })
      .catch(console.error);
  }

  // сохранение изменений по группе
  function handleSaveGroup() {
    if (!selectedGroupId) return;

    fetch(`/api/theory/task-groups/${selectedGroupId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: groupNameDraft,
        is_single: groupIsSingleDraft,
      }),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        setGroups(data || []);
      })
      .catch(console.error);
  }

  function handleDeleteGroup() {
    if (!selectedGroupId) return;
    if (!window.confirm("Удалить группу задач?")) return;

    fetch(`/api/theory/task-groups/${selectedGroupId}`, {
      method: "DELETE",
    })
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        const items = data || [];
        setGroups(items);

        const firstGroup = items[0] || null;
        const firstTask =
          firstGroup && firstGroup.tasks && firstGroup.tasks[0]
            ? firstGroup.tasks[0]
            : null;

        setSelectedGroupId(firstGroup ? firstGroup.task_group_id : null);
        setSelectedTaskId(firstTask ? firstTask.task_id : null);

        const expanded = items
          .filter((g) => !g.is_single)
          .map((g) => g.task_group_id);
        setExpandedGroupIds(expanded);
      })
      .catch(console.error);
  }

  // задачи
  function handleCreateTask() {
    if (!selectedGroupId) {
      alert("Сначала выберите группу");
      return;
    }
    const name = prompt("Название новой задачи:");
    if (!name) return;

    fetch(`/api/theory/task-groups/${selectedGroupId}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        const items = data || [];
        setGroups(items);

        const group = items.find(
          (g) => g.task_group_id === selectedGroupId
        );
        const lastTask =
          group && group.tasks && group.tasks.length
            ? group.tasks[group.tasks.length - 1]
            : null;

        setSelectedTaskId(lastTask ? lastTask.task_id : null);
      })
      .catch(console.error);
  }

  function handleSaveTask() {
    if (!selectedTaskId) return;

    fetch(`/api/theory/tasks/${selectedTaskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: taskNameDraft,
        group_id: selectedGroupId,
      }),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        setGroups(data || []);
      })
      .catch(console.error);
  }

  function handleDeleteTask() {
    if (!selectedTaskId) return;
    if (!window.confirm("Удалить задачу?")) return;

    fetch(`/api/theory/tasks/${selectedTaskId}`, {
      method: "DELETE",
    })
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        const items = data || [];
        setGroups(items);

        const group = items.find(
          (g) => g.task_group_id === selectedGroupId
        );
        const firstTask =
          group && group.tasks && group.tasks[0]
            ? group.tasks[0]
            : null;

        setSelectedTaskId(firstTask ? firstTask.task_id : null);
      })
      .catch(console.error);
  }

  // привязка теорий к задаче
  function handleToggleTheoryForTask(theoryId) {
    setSelectedTheoryIdsForTask((prev) => {
      if (prev.includes(theoryId)) {
        return prev.filter((id) => id !== theoryId);
      }
      return [...prev, theoryId];
    });
  }

  function handleSaveTaskTheories() {
    if (!selectedTaskId) return;

    fetch(`/api/theory/tasks/${selectedTaskId}/theories`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theory_ids: selectedTheoryIdsForTask }),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_tasks_theory_for_subject/${subjectId}`).then(
          (r) => r.json()
        )
      )
      .then((data) => {
        setGroups(data || []);
      })
      .catch(console.error);
  }

  return (
    <div className="form-main">
      {/* ЛЕВАЯ ЧАСТЬ: группы и задачи */}
      <div className="form-tree">
        <div className="form-tree__header">Группы задач</div>
        <div className="form-tree__scroll">
          {groups.map((g) => {
            const isSingle = !!g.is_single;
            const tasks = g.tasks || [];
            const singleTask = isSingle && tasks.length ? tasks[0] : null;

            if (isSingle && singleTask) {
              const isActive =
                selectedTaskId === singleTask.task_id ||
                selectedGroupId === g.task_group_id;

              return (
                <div key={g.task_group_id}>
                  <div
                    className={
                      isActive
                        ? "form-tree__item form-tree__item--active"
                        : "form-tree__item"
                    }
                    onClick={() => {
                      setSelectedGroupId(g.task_group_id);
                      setSelectedTaskId(singleTask.task_id);
                    }}
                  >
                    {g.group_name}
                  </div>
                </div>
              );
            }

            const isExpanded = expandedGroupIds.includes(g.task_group_id);

            return (
              <div key={g.task_group_id}>
                <div
                  className={
                    selectedGroupId === g.task_group_id
                      ? "form-tree__item form-tree__item--active"
                      : "form-tree__item"
                  }
                  onClick={() => {
                    setSelectedGroupId(g.task_group_id);
                    toggleGroupExpanded(g.task_group_id);
                  }}
                >
                  <span style={{ marginRight: 6 }}>
                    {isExpanded ? "▾" : "▸"}
                  </span>
                  {g.group_name}
                </div>

                {isExpanded &&
                  (g.tasks || []).map((t) => (
                    <div
                      key={t.task_id}
                      className={
                        selectedTaskId === t.task_id
                          ? "form-tree__item form-tree__item--active"
                          : "form-tree__item"
                      }
                      style={{ paddingLeft: 24 }}
                      onClick={() => {
                        setSelectedGroupId(g.task_group_id);
                        setSelectedTaskId(t.task_id);
                      }}
                    >
                      {t.task_name}
                    </div>
                  ))}
              </div>
            );
          })}
        </div>

        <button className="form-tree__add" onClick={handleCreateGroup}>
          + Добавить группу задач
        </button>
      </div>

      {/* ПРАВАЯ ЧАСТЬ: редактор + линкуемая теория, растянутая до низа */}
      <div className="form-editor" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
        {/* верх: группа + задача */}
        <div style={{ flex: "0 0 auto" }}>
          <div className="form-editor__header">Редактор задач</div>

          {/* Редактирование группы */}
          <div className="form-editor__field">
            <label>Группа</label>
            <input
              type="text"
              value={groupNameDraft}
              onChange={(e) => setGroupNameDraft(e.target.value)}
              disabled={!selectedGroupId}
            />
          </div>

          <div className="form-editor__field">
            <label>Одиночная</label>
            <input
              type="checkbox"
              style={{ marginLeft: 0 }}
              checked={groupIsSingleDraft}
              onChange={(e) => setGroupIsSingleDraft(e.target.checked)}
              disabled={!selectedGroupId}
            />
          </div>

          <div className="form-editor__actions">
            <button
              type="button"
              onClick={handleSaveGroup}
              disabled={!selectedGroupId}
            >
              Сохранить группу
            </button>
            <button
              type="button"
              className="form-editor__delete"
              onClick={handleDeleteGroup}
              disabled={!selectedGroupId}
            >
              Удалить группу
            </button>
          </div>

          {/* Редактирование задачи */}
          <div className="form-editor__field" style={{ marginTop: 12 }}>
            <label>Задача</label>
            <input
              type="text"
              value={taskNameDraft}
              onChange={(e) => setTaskNameDraft(e.target.value)}
              disabled={!selectedTaskId}
            />
          </div>

          <div className="form-editor__actions">
            <button
              type="button"
              onClick={handleCreateTask}
              disabled={!selectedGroupId}
            >
              + Добавить задачу
            </button>
            <button
              type="button"
              onClick={handleSaveTask}
              disabled={!selectedTaskId}
            >
              Сохранить задачу
            </button>
            <button
              type="button"
              className="form-editor__delete"
              onClick={handleDeleteTask}
              disabled={!selectedTaskId}
            >
              Удалить задачу
            </button>
          </div>
        </div>

        {/* низ: ЛИНКУЕМАЯ ТЕОРИЯ, тянется до низа и скроллится внутри */}
        <div
          style={{
            flex: "1 1 auto",
            minHeight: 0,
            marginTop: 16,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div className="form-editor__header">Линкуемая теория</div>

          <div
            className="form-editor__field"
            style={{ flex: 1, minHeight: 0, alignItems: "stretch" }}
          >
            <label></label>
            <div
              style={{
                flex: 1,
                minHeight: 0,
                maxHeight: "100%",
                overflowY: "auto",
              }}
            >
              <div
                className="form-types-select"
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "8px",
                }}
              >
                {theories.map((th) => (
                  <button
                    key={th.id}
                    type="button"
                    className={
                      selectedTheoryIdsForTask.includes(th.id)
                        ? "form-types-select__chip form-types-select__chip--active"
                        : "form-types-select__chip"
                    }
                    style={{
                      width: "100%",
                      justifyContent: "center",
                      padding: "8px 10px",
                      fontSize: "0.9rem",
                      whiteSpace: "normal",
                      textAlign: "center",
                    }}
                    onClick={() => handleToggleTheoryForTask(th.id)}
                    disabled={!selectedTaskId}
                  >
                    {th.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="form-editor__actions">
            <button
              type="button"
              onClick={handleSaveTaskTheories}
              disabled={!selectedTaskId}
            >
              Сохранить привязку теорий
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
