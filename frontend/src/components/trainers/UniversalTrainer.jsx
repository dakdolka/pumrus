import { useRef, useEffect } from 'react';
import { resolveOptionSet, useUniversalTrainer } from './useUniversalTrainer.js';
import './trainer.css';

const EMPTY_RESULT = { status: 'none', notice: null, displayContent: null };

// ─── Попап ────────────────────────────────────────────────────────────────────

function MistakesPopup({ title, mistakes, stats, onClose, onReset, showReset = false }) {
  return (
    <div className="trainer-popup-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="trainer-popup">
        <h2>{title}</h2>

        {stats && (
          <div className="trainer-stats">
            ✅ {stats.correct} &nbsp;|&nbsp; ❌ {stats.wrong} &nbsp;|&nbsp; ⬜ {stats.remaining}
          </div>
        )}

        {mistakes.length === 0 ? (
          <div className="trainer-no-mistakes">Ошибок нет 🎉</div>
        ) : (
          <div className="trainer-mistakes-list">
            {mistakes.map(({ item, result }) => (
              <div key={item.id} className="trainer-mistake-word">
                <div className="trainer-mistake-visible"
                     dangerouslySetInnerHTML={{ __html: item.content_visible }} />
                <div className="trainer-mistake-correct">→ {item.content_correct}</div>
                {result?.notice && (
                  <div className="trainer-mistake-notice">{result.notice}</div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="trainer-popup-close">
          {showReset && (
            <button className="trainer-button trainer-button--danger" onClick={onReset}>
              Сбросить
            </button>
          )}
          <button className="trainer-button" onClick={onClose}>
            {showReset ? 'Продолжить' : 'Закрыть'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Попап подтверждения сброса ───────────────────────────────────────────────

function ConfirmResetPopup({ onConfirm, onCancel }) {
  return (
    <div className="trainer-popup-overlay" onClick={e => e.target === e.currentTarget && onCancel()}>
      <div className="trainer-popup trainer-popup--compact">
        <h2>Сбросить прогресс?</h2>
        <p className="trainer-confirm-text">
          Текущая сессия будет закрыта, прогресс удалён. Начнём заново.
        </p>
        <div className="trainer-popup-close">
          <button className="trainer-button trainer-button--danger" onClick={onConfirm}>
            Сбросить
          </button>
          <button className="trainer-button" onClick={onCancel}>
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Нотис после ответа ───────────────────────────────────────────────────────

function NoticeToast({ notice, status }) {
  if (!notice) return null;
  return (
    <div className={`trainer-notice trainer-notice--${status}`}>
      {notice}
    </div>
  );
}

// ─── Кнопки опций (fixed внизу) ───────────────────────────────────────────────

function OptionsKeyboard({ options, onSelect, answered }) {
  return (
    <div className="spelling-keyboard">
      {options.map(opt => (
        <button
          key={opt.id}
          className={`spelling-key${answered ? ' spelling-key--disabled' : ''}`}
          disabled={answered}
          onClick={() => !answered && onSelect(opt)}
        >
          {opt.content}
        </button>
      ))}
    </div>
  );
}

// ─── Текстовый ввод (fixed внизу) ────────────────────────────────────────────

function TextKeyboard({ value, onChange, onSubmit, loading, answered }) {
  return (
    <div className="spelling-keyboard trainer-text-keyboard">
      <input
        className="trainer-text-input"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && onSubmit()}
        placeholder="Введите ответ…"
        disabled={answered || loading}
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
      />
      <button
        className={`spelling-key trainer-text-submit${loading ? ' spelling-key--disabled' : ''}`}
        onClick={onSubmit}
        disabled={answered || loading}
      >
        {loading ? <span className="task-select__item-spinner" /> : '→'}
      </button>
    </div>
  );
}

// ─── Один элемент задания ─────────────────────────────────────────────────────

function TaskItem({ item, result, isActive, index, onActivate }) {
  const safeResult = result ?? EMPTY_RESULT;
  const answered   = safeResult.status !== 'none';
  const ref        = useRef(null);

  useEffect(() => {
    if (isActive && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [isActive]);

  let cls = 'trainer-word-input';
  if (isActive)                        cls += ' trainer-word-input--active';
  if (safeResult.status === 'correct') cls += ' trainer-item--correct';
  if (safeResult.status === 'wrong')   cls += ' trainer-item--wrong';

  return (
    <div ref={ref} className={cls} onClick={() => !answered && onActivate(index)}>
      <span className="trainer-item-content">
        {safeResult.status === 'correct' ? (
          <span dangerouslySetInnerHTML={{ __html: safeResult.displayContent ?? item.content_correct }} />
        ) : safeResult.status === 'wrong' ? (
          <>
            <span
              className="trainer-item-strikethrough"
              dangerouslySetInnerHTML={{ __html: item.content_visible }}
            />
            <span className="trainer-item-correct-answer"> → {item.content_correct}</span>
          </>
        ) : (
          <span dangerouslySetInnerHTML={{ __html: item.content_visible }} />
        )}
      </span>

      {answered && (
        <span className={`trainer-item-badge trainer-item-badge--${safeResult.status}`}>
          {safeResult.status === 'correct' ? '✓' : '✗'}
        </span>
      )}
    </div>
  );
}

// ─── Пагинация ────────────────────────────────────────────────────────────────

function Pagination({ currentPage, totalPages, onPrev, onNext }) {
  if (totalPages <= 1) return null;
  return (
    <div className="trainer-page-nav">
      <button
        className="trainer-button trainer-button--small"
        onClick={onPrev}
        disabled={currentPage === 0}
      >
        ←
      </button>
      <span className="trainer-page-indicator">
        {currentPage + 1} / {totalPages}
      </span>
      <button
        className="trainer-button trainer-button--small"
        onClick={onNext}
        disabled={currentPage === totalPages - 1}
      >
        →
      </button>
    </div>
  );
}

// ─── Главный компонент ────────────────────────────────────────────────────────

export function UniversalTrainer({ task, userId, storageKey, onExit, exitRef, onFinish}) {
  const trainer = useUniversalTrainer({ task, userId, storageKey, onExit, exitRef, onFinish });

  const {
    items, results, setResults,
    activeIndex, setActiveIndex,
    currentPage, setCurrentPage,
    totalPages, start, end,
    inputValue, setInputValue, inputLoading,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showFinish,       setShowFinish,
    showConfirmReset, setShowConfirmReset,
    stats,
    answerWithOption, answerWithText,
    reset,
    collectMistakes,
    onExit: exit,
  } = trainer;

  const activeItem     = items[activeIndex] ?? null;
  const activeResult   = results[activeIndex] ?? EMPTY_RESULT;
  const activeAnswered = activeResult.status !== 'none';
  const optionSet      = activeItem ? resolveOptionSet(activeItem, task) : null;
  const hasOptions     = !!optionSet?.options?.length;

  const pageItems = items.slice(start, end);

  function handleOptionSelect(opt) {
    if (activeAnswered || activeIndex < start || activeIndex >= end) return;
    answerWithOption(activeIndex, opt);
  }

  function handleTextSubmit() {
    if (!inputValue.trim() || activeAnswered) return;
    answerWithText(activeIndex, inputValue);
  }

  // ── Сброс страницы (из попапа завершения страницы) ────
  function handlePageReset() {
    setShowPageMistakes(false);
    const next = [...results];
    for (let i = start; i < end; i++) next[i] = { ...EMPTY_RESULT };
    setResults(next);
    // Убираем страницу из shownPages — внутри хука через setResults сработает детект
  }

  return (
    <div className="trainer-container spelling-trainer-container">

      {/* ── Статистика ─────────────────────────────────── */}
      <div className="trainer-stats">
        ✅ {stats.correct} &nbsp;|&nbsp; ❌ {stats.wrong} &nbsp;|&nbsp; ⬜ {stats.remaining}
      </div>

      {/* ── Кнопки управления ──────────────────────────── */}
      <div className="trainer-controls trainer-controls--compact">
        <button
          className="trainer-button trainer-button--small"
          onClick={() => setShowAllMistakes(true)}
        >
          Ошибки ({stats.wrong})
        </button>
        <button
          className="trainer-button trainer-button--small trainer-button--danger"
          onClick={() => setShowConfirmReset(true)}
        >
          Сбросить
        </button>
      </div>

      {/* ── Пагинация ──────────────────────────────────── */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPrev={() => setCurrentPage(p => p - 1)}
        onNext={() => setCurrentPage(p => p + 1)}
      />

      {/* ── Нотис ──────────────────────────────────────── */}
      <NoticeToast notice={activeResult.notice} status={activeResult.status} />

      {/* ── Список элементов ───────────────────────────── */}
      <div className="trainer-words">
        {pageItems.map((item, i) => {
          const absIdx = start + i;
          return (
            <TaskItem
              key={item.id}
              item={item}
              task={task}
              result={results[absIdx] ?? EMPTY_RESULT}
              isActive={absIdx === activeIndex}
              index={absIdx}
              onActivate={idx => {
                setActiveIndex(idx);
                setInputValue('');
              }}
            />
          );
        })}
      </div>

      {/* ── Клавиатура ─────────────────────────────────── */}
      {hasOptions ? (
        <OptionsKeyboard
          options={optionSet.options}
          onSelect={handleOptionSelect}
          answered={activeAnswered}
        />
      ) : (
        <TextKeyboard
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleTextSubmit}
          loading={inputLoading}
          answered={activeAnswered}
        />
      )}

      {/* ── Попапы ─────────────────────────────────────── */}

      {showConfirmReset && (
        <ConfirmResetPopup
          onConfirm={reset}
          onCancel={() => setShowConfirmReset(false)}
        />
      )}

      {showPageMistakes && (
        <MistakesPopup
          title={`Страница ${currentPage + 1} завершена`}
          mistakes={collectMistakes(start, end)}
          stats={null}
          onClose={() => {
            setShowPageMistakes(false);
            if (currentPage < totalPages - 1) setCurrentPage(p => p + 1);
          }}
          onReset={handlePageReset}
          showReset
        />
      )}

      {showAllMistakes && (
        <MistakesPopup
          title="Все ошибки"
          mistakes={collectMistakes()}
          stats={stats}
          onClose={() => setShowAllMistakes(false)}
        />
      )}

      {showExitMistakes && (
        <MistakesPopup
          title="Ошибки за сессию"
          mistakes={collectMistakes()}
          stats={stats}
          onClose={() => {
            setShowExitMistakes(false);
            exit?.();
          }}
        />
      )}

      {showFinish && (
        <MistakesPopup
          title="Задание завершено! 🎉"
          mistakes={collectMistakes()}
          stats={stats}
          onClose={() => {
            setShowFinish(false);
            exit?.();
          }}
        />
      )}
    </div>
  );
}
