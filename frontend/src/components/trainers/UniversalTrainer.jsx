import { useRef, useEffect } from 'react';
import { resolveOptionSet, useUniversalTrainer } from './useUniversalTrainer.js';
import './trainer.css';

const EMPTY_RESULT  = { status: 'none', notice: null, displayContent: null };
const VOWELS_RU     = new Set(['а','е','ё','и','о','у','ы','э','ю','я']);
const DEFAULT_VOWELS = ['а', 'е', 'и', 'о', 'у', 'ы', 'ю', 'я'];

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
          <button className="trainer-button trainer-button--danger" onClick={onConfirm}>Сбросить</button>
          <button className="trainer-button" onClick={onCancel}>Отмена</button>
        </div>
      </div>
    </div>
  );
}

// ─── Нотис ────────────────────────────────────────────────────────────────────

function NoticeToast({ notice, status }) {
  if (!notice) return null;
  return <div className={`trainer-notice trainer-notice--${status}`}>{notice}</div>;
}

// ─── Клавиатура опций ─────────────────────────────────────────────────────────

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

// ─── Текстовый ввод ───────────────────────────────────────────────────────────

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
        autoComplete="off" autoCorrect="off" spellCheck={false}
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

// ─── Клавиатура словарных слов ────────────────────────────────────────────────

function DictionaryKeyboard({ letters, onLetter, onBackspace, answered, canBackspace }) {
  return (
    <div className="spelling-keyboard trainer-dict-keyboard">
      {letters.map((letter, i) => (
        <button
          key={i}
          className={`spelling-key trainer-dict-key${answered ? ' spelling-key--disabled' : ''}`}
          disabled={answered}
          onClick={() => !answered && onLetter(letter)}
        >
          {letter}
        </button>
      ))}
      <button
        className={`spelling-key trainer-dict-key--backspace${(answered || !canBackspace) ? ' spelling-key--disabled' : ''}`}
        disabled={answered || !canBackspace}
        onClick={() => !answered && canBackspace && onBackspace()}
      >
        ⌫
      </button>
    </div>
  );
}

// ─── Стандартный элемент (options / input) ────────────────────────────────────

function TaskItem({ item, result, isActive, index, onActivate }) {
  const safeResult = result ?? EMPTY_RESULT;
  const answered   = safeResult.status !== 'none';
  const ref        = useRef(null);

  useEffect(() => {
    if (isActive && ref.current)
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
            <span className="trainer-item-strikethrough"
                  dangerouslySetInnerHTML={{ __html: item.content_visible }} />
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

// ─── Элемент ударений ─────────────────────────────────────────────────────────

function StressItem({ item, result, isActive, index, onActivate, onVowelClick }) {
  const safeResult = result ?? EMPTY_RESULT;
  const answered   = safeResult.status !== 'none';
  const ref        = useRef(null);

  useEffect(() => {
    if (isActive && ref.current)
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [isActive]);

  // Ударная позиция — заглавная буква в content_correct
  const stressedPos = [...item.content_correct].findIndex(c => /[А-ЯЁ]/.test(c));
  const chars       = [...item.content_visible.toLowerCase()];

  let cls = 'trainer-word-input trainer-stress-item';
  if (isActive)                        cls += ' trainer-word-input--active';
  if (safeResult.status === 'correct') cls += ' trainer-item--correct';
  if (safeResult.status === 'wrong')   cls += ' trainer-item--wrong';

  return (
    <div ref={ref} className={cls} onClick={() => !answered && onActivate(index)}>
      <span className="trainer-item-content trainer-stress-word">
        {answered ? (
          chars.map((ch, i) =>
            i === stressedPos
              ? <span key={i} className={`trainer-stress-mark trainer-stress-mark--${safeResult.status}`}>{ch}</span>
              : <span key={i}>{ch}</span>
          )
        ) : (
          chars.map((ch, i) => {
            const isVowel = VOWELS_RU.has(ch);
            if (isVowel) {
              return (
                <span
                  key={i}
                  className={`trainer-stress-vowel${isActive ? ' trainer-stress-vowel--clickable' : ''}`}
                  onClick={e => {
                    e.stopPropagation();
                    if (isActive && !answered) onVowelClick(index, i, stressedPos);
                  }}
                >
                  {ch}
                </span>
              );
            }
            return <span key={i} className="trainer-stress-consonant">{ch}</span>;
          })
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

// ─── Элемент словарного слова ─────────────────────────────────────────────────

function DictionaryItem({ item, result, isActive, index, onActivate, filledLetters = [] }) {
  const safeResult = result ?? EMPTY_RESULT;
  const answered   = safeResult.status !== 'none';
  const ref        = useRef(null);

  useEffect(() => {
    if (isActive && ref.current)
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [isActive]);

  let cls = 'trainer-word-input trainer-dict-item';
  if (isActive)                        cls += ' trainer-word-input--active';
  if (safeResult.status === 'correct') cls += ' trainer-item--correct';
  if (safeResult.status === 'wrong')   cls += ' trainer-item--wrong';

  let gapIdx = 0;
  const display = [...item.content_visible].map((ch, i) => {
    if (ch === '_') {
      const filled        = filledLetters[gapIdx];
      const isCurrentGap  = gapIdx === filledLetters.length;
      const correctLetter = item.content_correct[i];
      gapIdx++;

      if (answered) {
        return (
          <span key={i} className="trainer-dict-gap trainer-dict-gap--answered">
            {correctLetter}
          </span>
        );
      }
      return (
        <span key={i} className={
          `trainer-dict-gap${
            filled            ? ' trainer-dict-gap--filled'
          : isCurrentGap && isActive ? ' trainer-dict-gap--current'
          : ' trainer-dict-gap--empty'}`
        }>
          {filled ?? '·'}
        </span>
      );
    }
    return <span key={i}>{ch}</span>;
  });

  return (
    <div ref={ref} className={cls} onClick={() => !answered && onActivate(index)}>
      <span className="trainer-item-content trainer-dict-word">
        {answered && safeResult.status === 'wrong' ? (
          <>
            <span className="trainer-item-strikethrough">
              {item.content_visible.replace(/_/g, '?')}
            </span>
            <span className="trainer-item-correct-answer"> → {item.content_correct}</span>
          </>
        ) : display}
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
      <button className="trainer-button trainer-button--small" onClick={onPrev} disabled={currentPage === 0}>←</button>
      <span className="trainer-page-indicator">{currentPage + 1} / {totalPages}</span>
      <button className="trainer-button trainer-button--small" onClick={onNext} disabled={currentPage === totalPages - 1}>→</button>
    </div>
  );
}

// ─── Главный компонент ────────────────────────────────────────────────────────

export function UniversalTrainer({ task, userId, storageKey, onExit, exitRef, onFinish }) {
  const trainer = useUniversalTrainer({ task, userId, storageKey, onExit, exitRef, onFinish });

  const {
    items, results, setResults,
    activeIndex, setActiveIndex,
    currentPage, setCurrentPage,
    totalPages, start, end,
    inputValue, setInputValue, inputLoading,
    dictionaryInputs,
    showPageMistakes, setShowPageMistakes,
    showAllMistakes,  setShowAllMistakes,
    showExitMistakes, setShowExitMistakes,
    showFinish,       setShowFinish,
    showConfirmReset, setShowConfirmReset,
    stats,
    answerWithOption, answerWithText,
    answerWithVowelClick,
    addDictionaryLetter, removeDictionaryLetter,
    reset, collectMistakes,
    onExit: exit,
  } = trainer;

  const trainerType  = task.trainer_type ?? 'options';
  const activeItem   = items[activeIndex] ?? null;
  const activeResult = results[activeIndex] ?? EMPTY_RESULT;
  const activeAnswered = activeResult.status !== 'none';
  const optionSet    = activeItem ? resolveOptionSet(activeItem, task) : null;
  const hasOptions   = !!optionSet?.options?.length;
  const pageItems    = items.slice(start, end);

  // Буквы для словарной клавиатуры — из option_set или дефолтные гласные
  const dictLetters = optionSet?.options?.length
    ? optionSet.options.map(o => o.content)
    : DEFAULT_VOWELS;

  const filledForActive = dictionaryInputs[activeIndex] ?? [];

  function handleOptionSelect(opt) {
    if (activeAnswered || activeIndex < start || activeIndex >= end) return;
    answerWithOption(activeIndex, opt);
  }

  function handleTextSubmit() {
    if (!inputValue.trim() || activeAnswered) return;
    answerWithText(activeIndex, inputValue);
  }

  function handlePageReset() {
    setShowPageMistakes(false);
    const next = [...results];
    for (let i = start; i < end; i++) next[i] = { ...EMPTY_RESULT };
    setResults(next);
  }

  // ── Рендер элемента ───────────────────────────────────
  function renderItem(item, absIdx) {
    const res = results[absIdx] ?? EMPTY_RESULT;
    const isActive = absIdx === activeIndex;
    const activate = idx => { setActiveIndex(idx); setInputValue(''); };

    if (trainerType === 'stress') {
      return (
        <StressItem
          key={item.id}
          item={item}
          result={res}
          isActive={isActive}
          index={absIdx}
          onActivate={activate}
          onVowelClick={answerWithVowelClick}
        />
      );
    }

    if (trainerType === 'dictionary') {
      return (
        <DictionaryItem
          key={item.id}
          item={item}
          result={res}
          isActive={isActive}
          index={absIdx}
          onActivate={activate}
          filledLetters={dictionaryInputs[absIdx] ?? []}
        />
      );
    }

    return (
      <TaskItem
        key={item.id}
        item={item}
        result={res}
        isActive={isActive}
        index={absIdx}
        onActivate={activate}
      />
    );
  }

  // ── Рендер клавиатуры ─────────────────────────────────
  function renderKeyboard() {
    if (trainerType === 'stress') return null;

    if (trainerType === 'dictionary') {
      return (
        <DictionaryKeyboard
          letters={dictLetters}
          onLetter={letter => addDictionaryLetter(activeIndex, letter)}
          onBackspace={() => removeDictionaryLetter(activeIndex)}
          answered={activeAnswered}
          canBackspace={filledForActive.length > 0}
        />
      );
    }

    if (hasOptions) {
      return (
        <OptionsKeyboard
          options={optionSet.options}
          onSelect={handleOptionSelect}
          answered={activeAnswered}
        />
      );
    }

    return (
      <TextKeyboard
        value={inputValue}
        onChange={setInputValue}
        onSubmit={handleTextSubmit}
        loading={inputLoading}
        answered={activeAnswered}
      />
    );
  }

  return (
    <div className="trainer-container spelling-trainer-container">

      <div className="trainer-stats">
        ✅ {stats.correct} &nbsp;|&nbsp; ❌ {stats.wrong} &nbsp;|&nbsp; ⬜ {stats.remaining}
      </div>

      <div className="trainer-controls trainer-controls--compact">
        <button className="trainer-button trainer-button--small" onClick={() => setShowAllMistakes(true)}>
          Ошибки ({stats.wrong})
        </button>
        <button className="trainer-button trainer-button--small trainer-button--danger" onClick={() => setShowConfirmReset(true)}>
          Сбросить
        </button>
      </div>

      <Pagination
        currentPage={currentPage} totalPages={totalPages}
        onPrev={() => setCurrentPage(p => p - 1)}
        onNext={() => setCurrentPage(p => p + 1)}
      />

      <NoticeToast notice={activeResult.notice} status={activeResult.status} />

      <div className="trainer-words">
        {pageItems.map((item, i) => renderItem(item, start + i))}
      </div>

      {renderKeyboard()}

      {showConfirmReset && <ConfirmResetPopup onConfirm={reset} onCancel={() => setShowConfirmReset(false)} />}

      {showPageMistakes && (
        <MistakesPopup
          title={`Страница ${currentPage + 1} завершена`}
          mistakes={collectMistakes(start, end)} stats={null}
          onClose={() => { setShowPageMistakes(false); if (currentPage < totalPages - 1) setCurrentPage(p => p + 1); }}
          onReset={handlePageReset} showReset
        />
      )}

      {showAllMistakes && (
        <MistakesPopup title="Все ошибки" mistakes={collectMistakes()} stats={stats}
          onClose={() => setShowAllMistakes(false)} />
      )}

      {showExitMistakes && (
        <MistakesPopup title="Ошибки за сессию" mistakes={collectMistakes()} stats={stats}
          onClose={() => { setShowExitMistakes(false); exit?.(); }} />
      )}

      {showFinish && (
        <MistakesPopup title="Задание завершено! 🎉" mistakes={collectMistakes()} stats={stats}
          onClose={() => { setShowFinish(false); exit?.(); }} />
      )}
    </div>
  );
}
