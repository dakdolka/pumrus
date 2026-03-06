import React, { useState } from 'react';
import './trainers.css';

export function TaskSelect({ tasks, trainerLabel, onSelect }) {
  const [loadingTaskId, setLoadingTaskId] = useState(null);

  async function handleSelect(task) {
    if (loadingTaskId) return;
    setLoadingTaskId(task.id);
    try {
      const full = await fetch(`/api/tasks/${task.id}`).then(r => r.json());
      onSelect(full);
    } catch {
      setLoadingTaskId(null);
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="task-select">
        <div className="task-select__empty" style={{ color: '#ffffff' }}>
          Нет доступных заданий для «{trainerLabel}»
        </div>
      </div>
    );
  }

  return (
    <div className="task-select">
      <div className="task-select__header" style={{ color: '#ffffff' }}>
        Выберите задание
      </div>
      {tasks.map(task => (
        <button
          key={task.id}
          className={`task-select__item${loadingTaskId === task.id ? ' task-select__item--loading' : ''}`}
          onClick={() => handleSelect(task)}
          disabled={!!loadingTaskId}
        >
          <span className="task-select__item-name" style={{ color: '#ffffff' }}>
            {task.name}
          </span>
          {loadingTaskId === task.id && <span className="task-select__item-spinner" />}
        </button>
      ))}
    </div>
  );
}
