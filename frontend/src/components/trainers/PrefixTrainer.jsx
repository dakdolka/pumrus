import React, { useState, useEffect, useRef } from 'react';
import './trainers.css';

const STORAGE_KEY = 'pre_pri_trainer_state_v2';

const wordsRaw = `
прИбывать в город
прЕбывать в городе
прИзреть сироту
прЕзирать врага
прИтворить дверь
прЕтворить мечту в жизнь
прИклонить голову (отдохнуть)
прЕклонить голову/колени (оказать уважение)
прИдать значение
прЕдать друга
прИходящий человек
прИходящее явление
прИтерпеться к боли
прЕтерпеть трудности
прЕёмник радиосигнала
прИемник ученика
прИставить к награде
светопрЕставление
прЕставился(человек)
прИвратник стоял
прЕвратности судьбы
прИложить вплотную
непрЕложная истина
прИдел в церкви
прЕдел возможностей
прЕуменьшать(очень) важность
прИуменьшать(немного) значение
прИоритет
прИвилегия
прИбаутка
прИвередливый
прИгожий
прИбор
прИличия
прИстойно
прИесться
прИказ
прИключение
прИкорнуть
прИсяга
прИтеснять
прИчина
прИчуда
прИтязание
прИрода
прИмер
прИческа
прИскорбно
прИволье
прИцел
прИмета
прИверженец
прИлежный
прИчиндалы
прИятный
прИватный
прИнцип
прИмат
прИмитив
прИгодный
прИсниться
прИсудить
прИзвание
прИсмотреть
прИспособить
прЕрогатива
прЕмбула
прЕпятствие
прЕпоны
прЕрия
прЕзент
прЕимущество
прЕисподняя
прЕгрешение
прЕнебрегать
прЕкословить
прЕпираться
прЕстол
прЕвратный
прЕпинания
прЕславутый
прЕследовать
прЕподаватель
прЕподнести
прЕпроводить
прЕподобный
прЕткновения камень
прЕсмыкаться
прЕпарировать
прЕлюдия
прЕмьера
прЕстиж
прЕзидент
прЕтензия
прЕзумпция
прЕвентативный
прЕлат
прЕвалировать
прЕзидиум
прЕтендент
прЕферанс
прЕцедент
прЕпарат
прЕодолеть
`.trim().split('\n');

function parseWord(word) {
  const chars = [...word];
  const check = [];
  chars.forEach((ch, i) => {
    if (ch.match(/[А-ЯЁ]/)) {
      check.push(i);
    }
  });
  return { original: word, lower: word.toLowerCase(), check };
}

export function PrefixTrainer() {
  const [words, setWords] = useState([]);
  const [letterStates, setLetterStates] = useState([]);
  const [stats, setStats] = useState({ total: 0, correct: 0, wrong: 0 });
  const [currentWord, setCurrentWord] = useState(0);
  const [currentLetter, setCurrentLetter] = useState(0);
  const [showMistakes, setShowMistakes] = useState(false);

  const inputRef = useRef(null);

  // Инициализация
  useEffect(() => {
    const saved = loadState();
    if (saved) {
      setWords(saved.words);
      setLetterStates(saved.letterStates);
      setStats(saved.stats);
    } else {
      reset();
    }
  }, []);

  // Сохранение состояния
  useEffect(() => {
    if (words.length > 0) {
      saveState({ words, letterStates, stats });
    }
  }, [words, letterStates, stats]);

  // Автофокус на первую пустую букву
  useEffect(() => {
    focusFirstEmpty();
  }, [letterStates]);

  function shuffleArray(arr) {
    return arr.sort(() => Math.random() - 0.5);
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {}
  }

  function reset() {
    const shuffled = shuffleArray([...wordsRaw.map(parseWord)]);
    const states = shuffled.map(word => 
      word.check.map(() => ({ done: false, correct: null, input: '' }))
    );
    const totalSlots = shuffled.reduce((sum, word) => sum + word.check.length, 0);
    
    setWords(shuffled);
    setLetterStates(states);
    setStats({ total: totalSlots, correct: 0, wrong: 0 });
    setCurrentWord(0);
    setCurrentLetter(0);
    localStorage.removeItem(STORAGE_KEY);
  }

  function focusFirstEmpty() {
    for (let w = 0; w < letterStates.length; w++) {
      for (let l = 0; l < letterStates[w].length; l++) {
        if (!letterStates[w][l].done) {
          setCurrentWord(w);
          setCurrentLetter(l);
          return;
        }
      }
    }
  }

  function handleInput(value) {
    if (!value || currentWord >= words.length) return;

    const word = words[currentWord];
    const letterIndex = currentLetter;
    const letters = letterStates[currentWord];

    if (letterIndex >= letters.length || letters[letterIndex].done) {
      focusFirstEmpty();
      return;
    }

    const charIndex = word.check[letterIndex];
    const correctChar = word.lower[charIndex];
    const isCorrect = value.toLowerCase() === correctChar;

    setLetterStates(prev => {
      const newStates = [...prev];
      newStates[currentWord] = [...newStates[currentWord]];
      newStates[currentWord][letterIndex] = {
        done: true,
        correct: isCorrect,
        input: value.toLowerCase(),
      };
      return newStates;
    });

    setStats(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      wrong: prev.wrong + (isCorrect ? 0 : 1),
    }));
  }

  function collectMistakes() {
    return words
      .map((word, i) => {
        const hasError = letterStates[i]?.some(state => state.done && !state.correct);
        if (!hasError) return null;
        
        const chars = [...word.lower];
        return chars.map((ch, j) => {
          if (word.check.includes(j)) {
            return { char: ch.toUpperCase(), highlight: true };
          }
          return { char: ch, highlight: false };
        });
      })
      .filter(Boolean);
  }

  const accuracy = stats.total ? Math.round((stats.correct / stats.total) * 100) : 0;

  return (
    <div className="trainer-container">
      <h1 className="trainer-title">ПРЕ / ПРИ</h1>

      <div className="trainer-controls">
        <button onClick={reset} className="trainer-button">Сбросить</button>
        <button onClick={() => setShowMistakes(true)} className="trainer-button">
          Показать ошибки
        </button>
      </div>

      <div className="trainer-stats">
        Всего букв: <span>{stats.total}</span>, 
        верно: <span style={{ color: 'green' }}>{stats.correct}</span>, 
        ошибок: <span style={{ color: 'red' }}>{stats.wrong}</span>, 
        точность: <span>{accuracy}%</span>
      </div>

      <main className="trainer-words">
        {words.map((word, wordIndex) => (
          <WordInput
            key={wordIndex}
            word={word}
            letterStates={letterStates[wordIndex] || []}
            isActive={currentWord === wordIndex}
            onInput={handleInput}
            inputRef={currentWord === wordIndex ? inputRef : null}
          />
        ))}
      </main>

      <div className="trainer-controls">
        <button onClick={reset} className="trainer-button">Сбросить</button>
        <button onClick={() => setShowMistakes(true)} className="trainer-button">
          Показать ошибки
        </button>
      </div>

      {showMistakes && (
        <MistakesPopup
          mistakes={collectMistakes()}
          onClose={() => setShowMistakes(false)}
        />
      )}
    </div>
  );
}

// Компонент слова с вводом
// В PrefixTrainer.jsx, в компоненте WordInput:

function WordInput({ word, letterStates, isActive, onInput }) {
  const hiddenInputRef = useRef(null);
  const chars = [...word.lower];
  let letterIndex = 0;

  function handleClick() {
    hiddenInputRef.current?.focus();
  }

  function handleInput(e) {
    const value = e.target.value;
    if (value && /[а-яёА-ЯЁ]/i.test(value)) {
      onInput(value);
    }
    e.target.value = '';
  }

  useEffect(() => {
    if (isActive) {
      hiddenInputRef.current?.focus();
    }
  }, [isActive]);

  return (
    <div
      className={`trainer-word-input ${isActive ? 'trainer-word-input--active' : ''}`}
      onClick={handleClick}
    >
      {chars.map((ch, charIndex) => {
        if (word.check.includes(charIndex)) {
          const state = letterStates[letterIndex];
          
          const className = `trainer-letter ${
            state?.done
              ? state.correct
                ? 'trainer-letter--correct'
                : 'trainer-letter--wrong'
              : ''
          }`;

          letterIndex++;

          return (
            <span key={charIndex} className={className}>
              {/* Если ошибка - показываем правильную букву сверху зелёным */}
              {state?.done && !state.correct && (
                <span className="trainer-letter-correct-above">{ch}</span>
              )}
              {/* Основная буква */}
              {state?.done ? state.input : '\u00A0'}
            </span>
          );
        }
        return <span key={charIndex} className="trainer-char">{ch}</span>;
      })}

      <input
        ref={hiddenInputRef}
        type="text"
        className="trainer-hidden-input"
        autoComplete="off"
        spellCheck="false"
        inputMode="text"
        onInput={handleInput}
      />
    </div>
  );
}

// Попап ошибок
function MistakesPopup({ mistakes, onClose }) {
  return (
    <div className="trainer-popup-overlay" onClick={onClose}>
      <div className="trainer-popup" onClick={e => e.stopPropagation()}>
        <h2>Ошибки</h2>
        <div className="trainer-mistakes-list">
          {mistakes.length === 0 ? (
            <div>Ошибок нет! 🎉</div>
          ) : (
            mistakes.map((chars, i) => (
              <div key={i} className="trainer-mistake-word">
                {chars.map((item, j) => (
                  <span 
                    key={j} 
                    style={{ color: item.highlight ? 'green' : 'inherit' }}
                  >
                    {item.char}
                  </span>
                ))}
              </div>
            ))
          )}
        </div>
        <div className="trainer-popup-close">
          <button onClick={onClose} className="trainer-button">Закрыть</button>
        </div>
      </div>
    </div>
  );
}
