import './trainer.css';

function groupTasks(tasks) {
  const groups   = {};
  const noGroup  = [];

  tasks.forEach(task => {
    if (task.task_group) {
      const gid = task.task_group.id;
      if (!groups[gid]) groups[gid] = { group: task.task_group, tasks: [] };
      groups[gid].tasks.push(task);
    } else {
      noGroup.push(task);
    }
  });

  // Группы с одним таском — разворачиваем в noGroup
  const result = [];

  Object.values(groups).forEach(({ group, tasks: gt }) => {
    if (gt.length === 1) {
      noGroup.push(gt[0]);
    } else {
      result.push({ type: 'group', group, tasks: gt });
    }
  });

  // noGroup — каждый таск как отдельный элемент
  noGroup.forEach(task => result.push({ type: 'single', task }));

  return result;
}

export function TaskSelect({ tasks, trainerLabel, onSelect }) {
  if (!tasks?.length) {
    return (
      <div className="task-select">
        <div className="task-select__empty">Нет доступных заданий</div>
      </div>
    );
  }

  const grouped = groupTasks(tasks);

  return (
    <div className="task-select">
      {grouped.map((entry, i) => {
        if (entry.type === 'single') {
          return (
            <button
              key={entry.task.id}
              className="task-select__item"
              onClick={() => onSelect(entry.task)}
            >
              <span className="task-select__item-name">{entry.task.name}</span>
            </button>
          );
        }

        // group с несколькими тасками
        return (
          <div key={entry.group.id} className="task-select__group">
            <div className="task-select__header">{entry.group.name}</div>
            {entry.tasks.map(task => (
              <button
                key={task.id}
                className="task-select__item task-select__item--indented"
                onClick={() => onSelect(task)}
              >
                <span className="task-select__item-name">{task.name}</span>
              </button>
            ))}
          </div>
        );
      })}
    </div>
  );
}
