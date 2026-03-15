import { useState } from 'react';
import { UniversalTrainer } from '../trainers/UniversalTrainer.jsx';
import '../trainers/trainer.css';

// ─── Попап резолва ────────────────────────────────────────────────────────────

function ResolvePopup({ correctItems, onResolve, onSkip }) {
  const [loading, setLoading] = useState(false);

  async function handle() {
    setLoading(true);
    await onResolve();
    setLoading(false);
  }

  return (
    <div className="trainer-popup-overlay">
      <div className="trainer-popup">
        <h2>Отработка завершена! 🎉</h2>

        {correctItems.length > 0 ? (
          <>
            <p className="trainer-confirm-text">
              Правильно решено: <strong>{correctItems.length}</strong>
            </p>

            <div className="trainer-mistakes-list">
              {correctItems.map(item => (
                <div key={item.id} className="trainer-mistake-word">
                  <div
                    className="trainer-mistake-visible"
                    dangerouslySetInnerHTML={{ __html: item.content_visible }}
                  />
                  <div className="trainer-mistake-correct">→ {item.content_correct}</div>
                </div>
              ))}
            </div>

            <p className="trainer-confirm-text" style={{ marginTop: 8 }}>
              Отметить эти ошибки как исправленные?
            </p>

            <div className="trainer-popup-close">
              <button
                className="trainer-button trainer-button--danger"
                onClick={onSkip}
                disabled={loading}
              >
                Не сейчас
              </button>
              <button
                className="trainer-button"
                onClick={handle}
                disabled={loading}
              >
                {loading
                  ? <><span className="task-select__spinner-inline" />&nbsp;Сохраняем…</>
                  : 'Да, исправлены!'
                }
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="trainer-confirm-text">
              На этот раз без правильных ответов — продолжай практиковаться!
            </p>
            <div className="trainer-popup-close">
              <button className="trainer-button" onClick={onSkip}>
                Закрыть
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Главный компонент ────────────────────────────────────────────────────────

export function PracticeTrainer({ task, mistakes, userId, onExit, onResolved }) {
  const [showResolvePopup, setShowResolvePopup] = useState(false);
  const [correctItems,     setCorrectItems]     = useState([]);
  const [results,          setResultsCache]     = useState(null);

  // Создаём псевдо-задание — только items из ошибок
  const mistakeItemIds = new Set(mistakes.map(m => m.mistake_item?.id).filter(Boolean));
  const filteredItems  = (task.items ?? []).filter(item => mistakeItemIds.has(item.id));

  const practiceTask = {
    ...task,
    id:    task.id,
    name:  `Отработка: ${task.name}`,
    items: filteredItems,
  };

  const storageKey = `practice_${task.id}_${userId}`;

  // Вызывается когда UniversalTrainer завершает задание (onExit из финиш-попапа)
  function handleFinish(finalResults) {
    // finalResults передаём через кастомный onExit
    setResultsCache(finalResults);

    // Собираем правильно решённые items
    const correct = filteredItems.filter((item, i) => {
      const r = finalResults?.[i];
      return r?.status === 'correct';
    });
    setCorrectItems(correct);
    setShowResolvePopup(true);
  }

  async function handleResolve() {
    try {
      // Резолвим все ошибки чьи items были правильно решены
      const correctIds = new Set(correctItems.map(i => i.id));
      const toResolve  = mistakes.filter(m => correctIds.has(m.mistake_item?.id));

      await Promise.all(
        toResolve.map(m =>
          fetch(`/api/users/mistakes/${m.id}/resolve`, { method: 'POST' })
        )
      );

      setShowResolvePopup(false);
      onResolved?.();
      onExit?.();
    } catch (e) {
      console.error('resolve failed', e);
    }
  }

  function handleSkip() {
    setShowResolvePopup(false);
    onExit?.();
  }

  if (filteredItems.length === 0) {
    return (
      <div className="mistakes-page">
        <div className="mistakes-empty">
          Нет элементов для отработки по этому заданию
        </div>
        <div className="trainer-controls">
          <button className="trainer-button" onClick={onExit}>Назад</button>
        </div>
      </div>
    );
  }

  return (
    <>
      <UniversalTrainer
        task={practiceTask}
        userId={userId}
        storageKey={storageKey}
        onExit={onExit}
        exitRef={null}
        onFinish={handleFinish}
      />

      {showResolvePopup && (
        <ResolvePopup
          correctItems={correctItems}
          onResolve={handleResolve}
          onSkip={handleSkip}
        />
      )}
    </>
  );
}
