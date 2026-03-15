import { useState, useEffect, useCallback } from 'react';
import '../trainers/trainer.css';
import './MistakesPage.css';

function plural(n, one, few, many) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
}

// ─── Строка ошибки ────────────────────────────────────────────────────────────

function MistakeRow({ mistake, onResolve }) {
  const [loading, setLoading] = useState(false);
  const item = mistake.mistake_item;

  async function handle() {
    setLoading(true);
    await onResolve(mistake.id);
    setLoading(false);
  }

  return (
    <div className={`mistake-row${mistake.is_resolved ? ' mistake-row--resolved' : ''}`}>
      <div className="mistake-row__body">
        <div
          className="mistake-row__visible"
          dangerouslySetInnerHTML={{ __html: item?.content_visible ?? '—' }}
        />
        <div className="mistake-row__correct">→ {item?.content_correct ?? '—'}</div>
        {mistake.chosen_option && !mistake.is_resolved && (
          <div className="mistake-row__chosen">
            Выбрано: <em>{mistake.chosen_option.content}</em>
          </div>
        )}
      </div>

      {mistake.is_resolved ? (
        <span className="mistake-row__done">✓</span>
      ) : (
        <button
          className={`mistake-row__btn${loading ? ' mistake-row__btn--loading' : ''}`}
          onClick={handle}
          disabled={loading}
          title="Отметить как исправленную"
        >
          {loading ? '…' : '✓'}
        </button>
      )}
    </div>
  );
}

// ─── Кнопка группы для отработки ─────────────────────────────────────────────

function PracticeGroupItem({ task, count, onClick }) {
  return (
    <button className="task-select__item" onClick={onClick}>
      <span className="task-select__item-name">{task.name}</span>
      <span className="practice-badge">
        {count} {plural(count, 'ошибка', 'ошибки', 'ошибок')}
      </span>
    </button>
  );
}

// ─── Главный компонент ────────────────────────────────────────────────────────

export function MistakesPage({ userId, onStartPractice, refreshKey }) {
  const [tab,        setTab]        = useState('mistakes');
  const [mistakes,   setMistakes]   = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [generating, setGenerating] = useState(false);
  const [groups,     setGroups]     = useState(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await fetch(`/api/users/mistakes/by-user/${userId}`).then(r => r.json());
      setMistakes(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
    setGroups(null);
  }, [load, refreshKey]);

  async function handleResolve(id) {
    try {
      const updated = await fetch(`/api/users/mistakes/${id}/resolve`, { method: 'POST' })
        .then(r => r.json());
      setMistakes(prev => prev.map(m => m.id === id ? updated : m));
      setGroups(null);
    } catch (e) { console.error(e); }
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
        const unresolved = mistakes.filter(m => !m.is_resolved);

        // Группируем по task_id из mistake_item
        const byTask = {};
        unresolved.forEach(m => {
        const tid = m.mistake_item?.task_id;
        if (!tid) return;
        if (!byTask[tid]) byTask[tid] = [];
        byTask[tid].push(m);
        });

        if (Object.keys(byTask).length === 0) {
        console.warn('Нет task_id в ошибках:', unresolved);
        setGroups([]);
        return;
        }

        // Загружаем задания параллельно
        const result = await Promise.all(
        Object.entries(byTask).map(async ([tid, ms]) => {
            const task = await fetch(`/api/tasks/general/${tid}`).then(r => r.json());
            return { task, mistakes: ms };
        })
        );

        // Фильтруем группы где нашлись items
        const valid = result.filter(({ task, mistakes: ms }) => {
        const ids = new Set(ms.map(m => m.mistake_item?.id).filter(Boolean));
        return (task.items ?? []).some(item => ids.has(item.id));
        });

        setGroups(valid);
    } catch (e) {
        console.error('handleGenerate error:', e);
    } finally {
        setGenerating(false);
    }
    }


  const unresolved = mistakes.filter(m => !m.is_resolved);
  const resolved   = mistakes.filter(m =>  m.is_resolved);

  return (
    <div className="mistakes-page">

      {/* ── Табы ───────────────────────────────────────── */}
      <div className="mistakes-tabs">
        <button
          className={`mistakes-tab${tab === 'mistakes' ? ' mistakes-tab--active' : ''}`}
          onClick={() => setTab('mistakes')}
        >
          Ошибки
          {mistakes.length > 0 && (
            <span className="mistakes-tab__badge">{mistakes.length}</span>
          )}
        </button>
        <button
          className={`mistakes-tab${tab === 'practice' ? ' mistakes-tab--active' : ''}`}
          onClick={() => setTab('practice')}
        >
          Отработка
          {unresolved.length > 0 && (
            <span className="mistakes-tab__badge mistakes-tab__badge--warn">
              {unresolved.length}
            </span>
          )}
        </button>
      </div>

      {/* ── Вкладка: Ошибки ────────────────────────────── */}
      {tab === 'mistakes' && (
        <div className="mistakes-list">
          {loading && <div className="mistakes-empty">Загрузка…</div>}

          {!loading && mistakes.length === 0 && (
            <div className="mistakes-empty">Ошибок пока нет 🎉</div>
          )}

          {!loading && mistakes.length > 0 && (
            <>
              {unresolved.length > 0 && (
                <div className="mistakes-section-title">
                  Нерешённые ({unresolved.length})
                </div>
              )}
              {unresolved.map(m => (
                <MistakeRow key={m.id} mistake={m} onResolve={handleResolve} />
              ))}

              {resolved.length > 0 && (
                <div className="mistakes-section-title mistakes-section-title--faded">
                  Исправленные ({resolved.length})
                </div>
              )}
              {resolved.map(m => (
                <MistakeRow key={m.id} mistake={m} onResolve={handleResolve} />
              ))}
            </>
          )}
        </div>
      )}

      {/* ── Вкладка: Отработка ─────────────────────────── */}
      {tab === 'practice' && (
        <div className="practice-section">
          {loading && <div className="mistakes-empty">Загрузка…</div>}

          {!loading && unresolved.length === 0 && (
            <div className="mistakes-empty">Все ошибки исправлены! 🎉</div>
          )}

          {!loading && unresolved.length > 0 && groups === null && (
            <div className="practice-generate">
              <div className="practice-generate__text">
                {unresolved.length}{' '}
                {plural(unresolved.length, 'нерешённая ошибка', 'нерешённые ошибки', 'нерешённых ошибок')}
              </div>
              <button
                className="trainer-button"
                onClick={handleGenerate}
                disabled={generating}
              >
                {generating
                  ? <><span className="task-select__spinner-inline" />&nbsp;Генерация…</>
                  : 'Сгенерировать задания'
                }
              </button>
            </div>
          )}

          {!loading && groups !== null && (
            <div className="task-select">
              <div className="task-select__header">Выберите задание для отработки</div>
              {groups.map(({ task, mistakes: gm }) => (
                <PracticeGroupItem
                  key={task.id}
                  task={task}
                  count={gm.length}
                  onClick={() => onStartPractice(task, gm)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
