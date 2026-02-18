import React, { useState, useEffect, useCallback } from 'react';
import './trainers.css';

const STORAGE_KEY = 'stress_trainer_state_v10';
const vowels = 'аеёиоуыэюя';

const wordsData =  ['аэропОрты', 'бАнты', 'бОроду', 'бухгАлтеров', 'вероисповЕдание', 'водопровОд', 'газопровОд', 'граждАнство', 'дефИс', 'дешевИзна', 'диспансЕр', 'договорЕнность', 'докумЕнт', 'досУг', 'еретИк', 'жалюзИ', 'знАчимость', 'Иксы', 'каталОг', 'квартАл', 'киломЕтр', 'кОнусов', 'корЫсть', 'крАны', 'кремЕнь', 'кремнЯ', 'лЕкторов', 'лОктя', 'лыжнЯ', 'мЕстностей', 'намЕрение', 'нарОст', 'нЕдруг', 'недУг', 'некролОг', 'нЕнависть', 'нефтепровОд', 'новостЕй', 'нОгтя', 'ногтЕй', 'Отрочество', 'партЕр', 'портфЕль', 'пОручни', 'придАное', 'призЫв', 'свЕкла', 'сирОты', 'созЫв', 'сосредотОчение', 'срЕдства', 'стАтуя', 'столЯр', 'тамОжня', 'тОрты', 'тУфля', 'цемЕнт', 'цЕнтнер', 'цепОчка', 'шАрфы', 'шофЕр', 'экспЕрт', 'вернА', 'знАчимый', 'красИвее', 'красИвейший', 'кУхонный', 'ловкА', 'мозаИчный', 'оптОвый', 'прозорлИвый', 'прозорлИва', 'слИвовый', 'бралА', 'бралАсь', 'взялА', 'взялАсь', 'влилАсь', 'ворвалАсь', 'воспринЯть', 'воспринялА', 'воссоздалА', 'вручИт', 'гналА', 'гналАсь', 'добралА', 'добралАсь', 'дождалАсь', 'дозвонИтся', 'дозИровать', 'ждалА', 'жилОсь', 'закУпорить', 'занЯть', 'заперлА', 'запломбировАть', 'защемИт', 'звалА', 'звонИт', 'кАшлянуть', 'клАла', 'клЕить', 'крАлась', 'кровоточИть', 'лгалА', 'лилА', 'лилАсь', 'навралА', 'наделИт', 'надорвалАсь', 'назвалАсь', 'накренИтся', 'налилА', 'нарвалА', 'начАть', 'обзвонИт', 'облегчИть', 'облегчИт', 'облилАсь', 'обнялАсь', 'обогналА', 'ободралА', 'ободрИть', 'ободрИться', 'обострИть', 'одолжИть', 'озлОбить', 'оклЕить', 'окружИт', 'опОшлить', 'освЕдомиться', 'освЕдомится', 'отбылА', 'отдалА', 'откУпорить', 'отозвалА', 'отозвалАсь', 'перезвонИт', 'перелилА', 'плодоносИть', 'пломбировАть', 'повторИт', 'позвалА', 'позвонИт', 'полилА', 'положИть', 'понЯть', 'послАла', 'прибЫть', 'принЯть', 'рвалА', 'сверлИт', 'снялА', 'совралА', 'создалА', 'сорвалА', 'сорИт', 'убралА', 'углубИть', 'укрепИт', 'чЕрпать', 'щемИт', 'щЕлкать', 'довезЕнный', 'зАгнутый', 'зАнятый', 'зАпертый', 'заселЕнный', 'кормЯщий', 'кровоточАщий', 'нажИвший', 'налИвший', 'нанЯвшийся', 'начАвший', 'нАчатый', 'низведЕнный', 'облегчЕнный', 'ободрЕнный', 'обострЕнный', 'отключЕнный', 'повторЕнный', 'поделЕнный', 'понЯвший', 'прИнятый', 'приручЕнный', 'прожИвший', 'снятА', 'сОгнутый', 'углублЕнный', 'закУпорив', 'начАв', 'начАвшись', 'отдАв', 'поднЯв', 'понЯв', 'прибЫв', 'создАв', 'вОвремя', 'дОверху', 'донЕльзя', 'дОнизу', 'дОсуха', 'зАсветло', 'зАтемно', 'красИвее', 'надОлго', 'ненадОлго'];

export function StressTrainer() {
  const [words, setWords] = useState([]);
  const [wordResults, setWordResults] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    wrong: 0,
  });
  const [showMistakes, setShowMistakes] = useState(false);

  // Загрузка состояния из localStorage
  useEffect(() => {
    const saved = loadState();
    if (saved) {
      setWords(saved.words);
      setWordResults(saved.wordResults);
      setStats({
        total: saved.total,
        correct: saved.correct,
        wrong: saved.wrong,
      });
    } else {
      reset();
    }
  }, []);

  // Сохранение состояния
  useEffect(() => {
    saveState({ words, wordResults, ...stats });
  }, [words, wordResults, stats]);

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
    const shuffled = shuffleArray([...wordsData]);
    setWords(shuffled);
    setWordResults(shuffled.map(() => ({ result: 'none', clicked: [] })));
    setStats({ total: shuffled.length, correct: 0, wrong: 0 });
    localStorage.removeItem(STORAGE_KEY);
  }

  function handleVowelClick(wordIndex, charIndex) {
    if (wordResults[wordIndex].result !== 'none') return;

    const originalWord = words[wordIndex];
    const chars = [...originalWord];
    
    // Найти ударную букву (заглавная)
    const correctIndex = chars.findIndex(ch => ch !== ch.toLowerCase());
    if (correctIndex === -1) return;

    const isCorrect = charIndex === correctIndex;
    
    setWordResults(prev => {
      const newResults = [...prev];
      newResults[wordIndex] = {
        result: isCorrect ? 'correct' : 'wrong',
        clicked: [...newResults[wordIndex].clicked, charIndex],
        correctIndex,
      };
      return newResults;
    });

    setStats(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      wrong: prev.wrong + (isCorrect ? 0 : 1),
    }));
  }

  function collectMistakes() {
    return words
      .map((word, i) => ({
        word,
        result: wordResults[i]?.result,
      }))
      .filter(item => item.result === 'wrong');
  }

  const accuracy = stats.total ? Math.round((stats.correct / stats.total) * 100) : 0;

  return (
    <div className="trainer-container">
      {/* <h1 className="trainer-title">Орфоэпический тест</h1> */}

      {/* Кнопки сверху */}
      <div className="trainer-controls">
        <button onClick={reset} className="trainer-button">
          Сбросить
        </button>
        <button onClick={() => setShowMistakes(true)} className="trainer-button">
          Показать ошибки
        </button>
      </div>

      {/* Статистика */}
      <div className="trainer-stats">
        Всего слов: <span>{stats.total}</span>, 
        верно: <span style={{ color: 'green' }}>{stats.correct}</span>, 
        ошибок: <span style={{ color: 'red' }}>{stats.wrong}</span>, 
        точность: <span>{accuracy}%</span>
      </div>

      {/* Слова */}
      <main className="trainer-words">
        {words.map((word, wordIndex) => {
          const result = wordResults[wordIndex];
          return (
            <WordDisplay
              key={wordIndex}
              word={word}
              result={result}
              onVowelClick={charIndex => handleVowelClick(wordIndex, charIndex)}
            />
          );
        })}
      </main>

      {/* Кнопки снизу */}
      <div className="trainer-controls">
        <button onClick={reset} className="trainer-button">
          Сбросить
        </button>
        <button onClick={() => setShowMistakes(true)} className="trainer-button">
          Показать ошибки
        </button>
      </div>

      {/* Попап ошибок */}
      {showMistakes && (
        <MistakesPopup
          mistakes={collectMistakes()}
          onClose={() => setShowMistakes(false)}
        />
      )}
    </div>
  );
}

// Компонент отображения слова
function WordDisplay({ word, result, onVowelClick }) {
  const chars = [...word];
  const correctIndex = chars.findIndex(ch => ch !== ch.toLowerCase());

  return (
    <div 
      className={`trainer-word-display ${result?.result !== 'none' ? 'trainer-word-display--done' : ''}`}
    >
      {chars.map((ch, charIndex) => {
        const lowerCh = ch.toLowerCase();
        const isVowel = vowels.includes(lowerCh);
        
        if (!isVowel) {
          return <span key={charIndex} className="trainer-char">{lowerCh}</span>;
        }

        const isCorrect = charIndex === correctIndex;
        const wasClicked = result?.clicked?.includes(charIndex);
        const isWrongClick = wasClicked && !isCorrect && result?.result === 'wrong';
        
        let displayChar = lowerCh;
        let className = 'trainer-vowel-slot';

        if (result?.result === 'correct' && isCorrect) {
          className += ' trainer-vowel-slot--correct';
          displayChar = lowerCh.toUpperCase();
        } else if (result?.result === 'wrong') {
          if (isWrongClick) {
            className += ' trainer-vowel-slot--wrong';
            // 🆕 НЕ дублируем букву - просто зачёркиваем
          } else if (isCorrect) {
            className += ' trainer-vowel-slot--correct';
            displayChar = lowerCh.toUpperCase();
          }
        } else {
          className += ' trainer-vowel-slot--clickable';
        }

        return (
          <span
            key={charIndex}
            className={className}
            onClick={() => result?.result === 'none' && onVowelClick(charIndex)}
          >
            {/* 🆕 Зачёркивание через CSS */}
            {displayChar}
          </span>
        );
      })}
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
            mistakes.map(({ word }, i) => {
              const chars = [...word];
              return (
                <div key={i} className="trainer-mistake-word">
                  {chars.map((ch, j) => {
                    if (ch !== ch.toLowerCase()) {
                      return <span key={j} style={{ color: 'green' }}>{ch}</span>;
                    }
                    return <span key={j}>{ch.toLowerCase()}</span>;
                  })}
                </div>
              );
            })
          )}
        </div>
        <div className="trainer-popup-close">
          <button onClick={onClose} className="trainer-button">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}


