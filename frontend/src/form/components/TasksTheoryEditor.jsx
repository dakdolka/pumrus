import React, { useEffect, useState } from "react";

/**
 * props:
 *  - subjectId: number
 *  - theories: список теорий по предмету (из FormApp)
 */
export function TasksTheoryEditor({ subjectId, theories }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const [groupNameDraft, setGroupNameDraft] = useState("");
  const [groupIsSingleDraft, setGroupIsSingleDraft] = useState(false);

  const [taskNameDraft, setTaskNameDraft] = useState("");
  const [selectedTheoryIdsForTask, setSelectedTheoryIdsForTask] = useState([]);

  // загрузка групп/тасков для предмета
  useEffect(() => {
    if (!subjectId) {
      setGroups([]);
      setSelectedGroupId(null);
      setSelectedTaskId(null);
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
          group && group.tasks && group.tasks[0] ? group.tasks[0] : null;

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
      <div className="form-tree">
        <div className="form-tree__header">Группы и задачи</div>
        <div className="form-tree__scroll">
          {groups.map((g) => (
            <div key={g.task_group_id}>
              <div
                className={
                  selectedGroupId === g.task_group_id
                    ? "form-tree__item form-tree__item--active"
                    : "form-tree__item"
                }
                onClick={() => {
                  setSelectedGroupId(g.task_group_id);
                  setSelectedTaskId(null);
                }}
              >
                <span className="form-tree__content">
                  {g.group_name} {g.is_single ? "(single)" : ""}
                </span>
              </div>

              {selectedGroupId === g.task_group_id && (
                <div style={{ marginLeft: 16 }}>
                  {(g.tasks || []).map((t) => (
                    <div
                      key={t.task_id}
                      className={
                        selectedTaskId === t.task_id
                          ? "form-tree__item form-tree__item--active"
                          : "form-tree__item"
                      }
                      onClick={() => {
                        setSelectedGroupId(g.task_group_id);
                        setSelectedTaskId(t.task_id);
                      }}
                    >
                      <span className="form-tree__content">
                        {t.task_name}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <button className="form-tree__add" onClick={handleCreateGroup}>
          + Добавить группу
        </button>
        <button className="form-tree__add" onClick={handleCreateTask}>
          + Добавить задачу
        </button>
      </div>

      <div className="form-editor">
        <div className="form-editor__header">Редактор группы / задачи</div>

        <div className="form-editor__field">
          <label>Группа:</label>
          <input
            type="text"
            value={groupNameDraft}
            onChange={(e) => setGroupNameDraft(e.target.value)}
          />
          <label>
            <input
              type="checkbox"
              checked={groupIsSingleDraft}
              onChange={(e) => setGroupIsSingleDraft(e.target.checked)}
            />
            single
          </label>
        </div>

        <div className="form-editor__actions">
          <button onClick={handleSaveGroup} disabled={!selectedGroupId}>
            Сохранить группу
          </button>
          <button
            onClick={handleDeleteGroup}
            disabled={!selectedGroupId}
            className="form-editor__delete"
          >
            Удалить группу
          </button>
        </div>

        <hr />

        <div className="form-editor__field">
          <label>Задача:</label>
          <input
            type="text"
            value={taskNameDraft}
            onChange={(e) => setTaskNameDraft(e.target.value)}
          />
        </div>

        <div className="form-editor__actions">
          <button onClick={handleSaveTask} disabled={!selectedTaskId}>
            Сохранить задачу
          </button>
          <button
            onClick={handleDeleteTask}
            disabled={!selectedTaskId}
            className="form-editor__delete"
          >
            Удалить задачу
          </button>
        </div>

        <hr />

        <div className="form-editor__header">Теория для задачи</div>
        <div
          className="form-editor__field form-editor__field--textarea"
          style={{ flexDirection: "column", alignItems: "flex-start" }}
        >
          <div
            style={{
              maxHeight: 200,
              overflowY: "auto",
              width: "100%",
            }}
          >
            {theories.map((th) => {
              const checked = selectedTheoryIdsForTask.includes(th.id);
              return (
                <label key={th.id} style={{ display: "block" }}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => handleToggleTheoryForTask(th.id)}
                  />{" "}
                  {th.name}
                </label>
              );
            })}
          </div>
        </div>

        <div className="form-editor__actions">
          <button onClick={handleSaveTaskTheories} disabled={!selectedTaskId}>
            Сохранить теории задачи
          </button>
        </div>
      </div>
    </div>
  );
}
