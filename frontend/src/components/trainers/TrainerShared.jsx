import React from 'react';

// blur после клика — сбрасывает выделение кнопки (пункт 6)
const b = e => e.currentTarget.blur();

export function TrainerStats({ stats, label = 'слов' }) {
  const accuracy = stats.total ? Math.round((stats.correct / stats.total) * 100) : 0;
  return (
    <div className="trainer-stats">
      Всего {label}: <span>{stats.total}</span>,{' '}
      верно: <span style={{ color: 'green' }}>{stats.correct}</span>,{' '}
      ошибок: <span style={{ color: 'red' }}>{stats.wrong}</span>,{' '}
      точность: <span>{accuracy}%</span>
    </div>
  );
}

// Компактные кнопки управления (пункт 2)
export function TrainerControls({ onResetAll, onResetPage, onMistakes }) {
  return (
    <div className="trainer-controls trainer-controls--compact">
      <button className="trainer-button trainer-button--small" onClick={e => { b(e); onResetAll(); }}><b>↺</b> Всё</button>
      <button className="trainer-button trainer-button--small" onClick={e => { b(e); onResetPage(); }}><b>↺</b> Страницу</button>
      <button className="trainer-button trainer-button--small" onClick={e => { b(e); onMistakes(); }}>Ошибки</button>
    </div>
  );
}

export function PageNav({ currentPage, totalPages, onPrev, onNext }) {
  return (
    <div className="trainer-page-nav">
      <button className="trainer-button" onClick={e => { b(e); onPrev(); }} disabled={currentPage === 0}>←</button>
      <span className="trainer-page-indicator">{currentPage + 1} / {totalPages}</span>
      <button className="trainer-button" onClick={e => { b(e); onNext(); }} disabled={currentPage >= totalPages - 1}>→</button>
    </div>
  );
}

// stats теперь отображается внутри попапа (пункт 1)
// renderMistake(item) → JSX
export function MistakesPopup({
  mistakes,
  onClose,
  renderMistake,
  title = 'Ошибки',
  stats,
  statsLabel = 'слов',
  isExit = false,
}) {
  return (
    <div className="trainer-popup-overlay" onClick={onClose}>
      <div className="trainer-popup" onClick={e => e.stopPropagation()}>
        <h2>{title}</h2>
        {stats && <TrainerStats stats={stats} label={statsLabel} />}
        <div className="trainer-mistakes-list">
          {mistakes.length === 0
            ? <div>Ошибок нет! 🎉</div>
            : mistakes.map((item, i) => (
                <div key={i} className="trainer-mistake-word">
                  {renderMistake(item)}
                </div>
              ))
          }
        </div>
        <div className="trainer-popup-close">
          <button
            onClick={e => { b(e); onClose(); }}
            className="trainer-button"
          >
            {isExit ? 'Выйти' : 'Закрыть'}   {/* текст для ясности */}
          </button>
        </div>
      </div>
    </div>
  );
}


export function ConfirmPopup({ message, onConfirm, onCancel }) {
  return (
    <div className="trainer-popup-overlay" onClick={onCancel}>
      <div className="trainer-popup" onClick={e => e.stopPropagation()}>
        <h2>Подтверждение</h2>
        <p className="trainer-confirm-message">{message}</p>
        <div className="trainer-popup-close">
          <button onClick={e => { b(e); onConfirm(); }} className="trainer-button">Да</button>
          <button onClick={e => { b(e); onCancel(); }} className="trainer-button">Отмена</button>
        </div>
      </div>
    </div>
  );
}
