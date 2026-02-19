import React, { useState, useEffect, useRef } from 'react';
import './trainers.css';

const STORAGE_KEY = 'spelling_trainer_state_v2';
const wordsData = [
  { word: '(в)виду болезни не пришел', correct: 'solid' },
  { word: 'иметь (в)виду', correct: 'separate' },
  { word: '(в)виду города', correct: 'separate' },
  { word: '(в)место пирога купить мороженое', correct: 'solid' },
  { word: '(в)место назначения', correct: 'separate' },
  { word: '(в)следствие болезни остался дома', correct: 'solid' },
  { word: '(в)следствии допущены ошибки', correct: 'separate' },
  { word: 'птица (на)подобие вороны', correct: 'solid' },
  { word: 'задача (на)подобие треугольников', correct: 'separate' },
  { word: 'поговорить (на)счет работы', correct: 'solid' },
  { word: 'положить деньги (на)счет', correct: 'separate' },
  { word: 'всматриваться (в)след', correct: 'separate' },
  { word: 'идти (в)след за другом', correct: 'solid' },
  { word: '(на)встречу ветру', correct: 'solid' },
  { word: 'идти (на)встречу к другу', correct: 'separate' },
  { word: '(в)связи с', correct: 'separate' },
  { word: '(в)отличие от', correct: 'separate' },
  { word: '(в)целях', correct: 'separate' },
  { word: '(в)силу', correct: 'separate' },
  { word: '(в)мерах', correct: 'separate' },
  { word: '(в)течение', correct: 'separate' },
  { word: '(в)продолжение', correct: 'separate' },
  { word: '(на)протяжении', correct: 'separate' },
  { word: '(в)заключение', correct: 'separate' },
  { word: '(в)результате', correct: 'separate' },
  { word: '(за)исключением', correct: 'separate' },
  { word: '(за)неимением', correct: 'separate' },
  { word: '(за)счет', correct: 'separate' },
  { word: '(по)причине', correct: 'separate' },
  { word: 'птица (в)роде вороны', correct: 'solid' },
  { word: 'согласовать (в)роде и числе', correct: 'separate' },
  { word: '(что)бы сдать ЕГЭ, нужно готовиться', correct: 'solid' },
  { word: '(что)бы приготовить?', correct: 'separate' },
  { word: '(что)бы он ни делал, всё получалось', correct: 'separate' },
  { word: '(то)же самое', correct: 'separate' },
  { word: 'одно и то(же)', correct: 'separate' },
  { word: 'он ел то(же), что и вчера', correct: 'separate' },
  { word: 'я то(же) приеду', correct: 'solid' },
  { word: 'вы (так)же ходили в театр сегодня?', correct: 'solid' },
  { word: 'мы поступили так(же)', correct: 'separate' },
  { word: 'было пасмурно, при(чем) ещё дождь моросил', correct: 'solid' },
  { word: '(при)чем же ты останешься?', correct: 'separate' },
  { word: '(при)чем здесь это?', correct: 'separate' },
  { word: 'было пасмурно, при(том) ещё дождь моросил', correct: 'solid' },
  { word: 'при(том) доме есть аптека', correct: 'separate' },
  { word: 'путь тяжелый, (за)то дорога красивая', correct: 'solid' },
  { word: 'спрячься (за)то дерево', correct: 'separate' },
  { word: '(за)чем вы здесь?', correct: 'solid' },
  { word: '(за)чем пойдешь, то и найдешь', correct: 'separate' },
  { word: '(от)чего ты плачешь?', correct: 'solid' },
  { word: '(от)чего стоит оттолкнуться?', correct: 'separate' },
  { word: 'мы проспали, по(тому) опоздали', correct: 'solid' },
  { word: 'мы пойдем (по)тому пути', correct: 'separate' },
  { word: '(по)чем сейчас картофель?', correct: 'solid' },
  { word: '(по)чем мне перебраться на тот берег, по мостику', correct: 'separate' },
  { word: 'и(так), все кончено', correct: 'solid' },
  { word: 'и(так) продолжалось долго', correct: 'separate' },
  { word: '(пол)тарелки', correct: 'solid' },
  { word: '(пол)часа', correct: 'solid' },
  { word: '(полу)месяц', correct: 'solid' },
  { word: '(в)(пол)голоса', correct: 'solid' },
  { word: '(в)(пол)оборота', correct: 'solid' },
  { word: 'как(будто)', correct: 'separate' },
  { word: '(как)раз', correct: 'separate' },
  { word: '(вряд)ли', correct: 'separate' },
  { word: '(все)равно', correct: 'separate' },
  { word: '(в)пустую комнату', correct: 'separate' },
  { word: 'работать (в)пустую', correct: 'solid' },
  { word: '(на)боковую', correct: 'separate' },
  { word: '(на)попятную', correct: 'separate' },
  { word: '(на)мировую', correct: 'separate' },
  { word: '(в)открытую', correct: 'separate' },
  { word: '(до)красна', correct: 'solid' },
  { word: '(с)лева', correct: 'solid' },
  { word: '(из)далека', correct: 'solid' },
  { word: '(на)право', correct: 'solid' },
  { word: '(в)лево', correct: 'solid' },
  { word: '(на)сколько лучше?', correct: 'solid' },
  { word: '(на)сколько дней?', correct: 'separate' },
  { word: '(не)даром ты здесь', correct: 'solid' },
  { word: '(не)даром тебе это досталось, а за деньги', correct: 'separate' },
  { word: 'прогуляться (по)осеннему лесу', correct: 'separate' },
  { word: 'волк(волком)', correct: 'separate' },
  { word: 'чин(чином)', correct: 'separate' },
  { word: '(во)всю стараться', correct: 'solid' },
  { word: '(во)всю силу работать', correct: 'separate' },
  { word: '(тот)час решил', correct: 'solid' },
  { word: 'в(тот) час прийти', correct: 'separate' },
  { word: '(на)завтра будет дождь', correct: 'solid' },
  { word: 'перенести дела (на)завтра', correct: 'separate' },
  { word: 'попал в музей (в)первые', correct: 'solid' },
  { word: '(в)первые ряды', correct: 'separate' },
  { word: 'смотрю (в)даль моря', correct: 'separate' },
  { word: 'глядим (в)даль', correct: 'solid' },
  { word: '(с)начала подумай', correct: 'solid' },
  { word: '(с)начала романа было все понятно', correct: 'separate' },
  { word: '(по)двое', correct: 'separate' },
  { word: '(по)одному', correct: 'separate' },
  { word: '(по)одиночке', correct: 'solid' },
  { word: '(в)одиночку', correct: 'separate' },
  { word: '(в)троем', correct: 'solid' },
  { word: '(на)двое', correct: 'solid' },
  { word: 'отложить дела (на)утро', correct: 'separate' },
  { word: '(на)утро обещала сделать', correct: 'solid' },
  { word: 'уснул (под)утро', correct: 'separate' },
  { word: '(с)утра читаю', correct: 'separate' },
  { word: '(без)конца', correct: 'separate' },
  { word: '(под)конец', correct: 'separate' },
  { word: '(до)конца', correct: 'separate' },
  { word: '(в)обнимку', correct: 'separate' },
  { word: '(в)обтяжку', correct: 'separate' },
  { word: '(в)охапку', correct: 'separate' },
  { word: '(без)устали', correct: 'separate' },
  { word: '(без)удержу', correct: 'separate' },
  { word: '(в)дребезги', correct: 'solid' },
  { word: '(на)тощак', correct: 'solid' },
  { word: '(ис)(под)тишка', correct: 'solid' },
  { word: '(в)догонку', correct: 'solid' },
  { word: '(до)тла', correct: 'solid' },
  { word: '(с)просонья', correct: 'solid' },
  { word: '(на)спех', correct: 'solid' },
  { word: '(на)угад', correct: 'solid' },
  { word: '(на)чеку', correct: 'solid' },
  { word: '(в)потемках', correct: 'separate' },
  { word: '(в)потьмах', correct: 'solid' },
  { word: '(на)радостях', correct: 'separate' },
  { word: '(на)сносях', correct: 'separate' },
  { word: '(в)сердцах', correct: 'separate' },
  { word: '(в)горячах', correct: 'solid' },
  { word: 'бок(о)бок', correct: 'separate' },
  { word: '(с)глазу(на)глаз', correct: 'separate' },
  { word: '(в)конце(концов)', correct: 'separate' },
  { word: '(с)лету', correct: 'separate' },
  { word: '(с)ходу', correct: 'separate' },
  { word: '(на)миг', correct: 'separate' },
  { word: '(в)миг', correct: 'solid' },
  { word: '(на)цыпочках', correct: 'separate' },
  { word: '(на)бегу', correct: 'separate' },
  { word: '(в)последствии', correct: 'solid' },
  { word: '(в)следствие', correct: 'solid' },
  { word: '(в)общем', correct: 'separate' },
  { word: '(в)целом', correct: 'separate' },
  { word: '(в)сецело', correct: 'solid' },
  { word: '(в)прочем', correct: 'solid' },
  { word: 'взять книгу (под)мышку', correct: 'separate' },
  { word: 'область (под)мышек', correct: 'solid' },
  { word: 'лечу (за)границу', correct: 'separate' },
  { word: 'торгую с (за)границей', correct: 'solid' },
  { word: '(в)конец обессилела', correct: 'solid' },
  { word: '(в)конец очереди', correct: 'separate' },
  { word: '(на)конец пришли!', correct: 'solid' },
  { word: 'перенести (на)конец месяца', correct: 'separate' },
  { word: 'сделать (во)время', correct: 'solid' },
  { word: 'храпит (во)время сна', correct: 'separate' },
  { word: '(в)праве знать', correct: 'solid' },
  { word: 'доля (в)праве собственности', correct: 'separate' },
  { word: '(на)силу удержал', correct: 'solid' },
  { word: 'надеятся (на)силу друзей', correct: 'separate' },
  { word: 'факты (на)лицо', correct: 'solid' },
  { word: 'нанести крем (на)лицо', correct: 'separate' },
  { word: 'сделал (на)зло', correct: 'solid' },
  { word: '(на)зло нельзя отвечать', correct: 'separate' },
  { word: 'биться (на)смерть', correct: 'solid' },
  { word: 'реакция (на)смерть поэта', correct: 'separate' },
  { word: 'чихнуть несколько раз (к)ряду', correct: 'solid' },
  { word: '(к)ряду чисел прибавить два', correct: 'separate' },
  { word: 'замахнуться (с)плеча', correct: 'solid' },
  { word: 'снять попугая (с)плеча', correct: 'separate' },
  { word: 'взять кофе (на)вынос', correct: 'solid' },
  { word: 'смотрю (на)вынос торта', correct: 'separate' },
  { word: 'смотрю (на)прокат велосипедов', correct: 'separate' },
  { word: 'взять велосипед (на)прокат', correct: 'solid' },
];

function parseParts(str) {
  const parts = [];
  const regex = /\(([^)]+)\)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(str)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', value: str.slice(lastIndex, match.index) });
    }
    parts.push({ type: 'marker', value: match[1] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < str.length) {
    parts.push({ type: 'text', value: str.slice(lastIndex) });
  }

  return parts;
}

function resolveWord(str, correct) {
  const parts = parseParts(str);
  const sep = correct === 'separate' ? ' ' : '';
  return parts.map(p => p.value).join(sep);
}


function shuffleArray(arr) {
  return [...arr].sort(() => Math.random() - 0.5);
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveState(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {}
}

export function SpellingTrainer() {
  const [words, setWords] = useState([]);
  const [wordResults, setWordResults] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [stats, setStats] = useState({ total: 0, correct: 0, wrong: 0 });
  const [showMistakes, setShowMistakes] = useState(false);
  const activeRef = useRef(null);

  useEffect(() => {
    const saved = loadState();
    if (saved) {
      setWords(saved.words);
      setWordResults(saved.wordResults);
      setActiveIndex(saved.activeIndex ?? 0);
      setStats({ total: saved.total, correct: saved.correct, wrong: saved.wrong });
    } else {
      reset();
    }
  }, []);

  useEffect(() => {
    saveState({ words, wordResults, activeIndex, ...stats });
  }, [words, wordResults, activeIndex, stats]);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [activeIndex]);

  function reset() {
    const shuffled = shuffleArray(wordsData);
    setWords(shuffled);
    setWordResults(shuffled.map(() => ({ result: 'none', chosen: null })));
    setActiveIndex(0);
    setStats({ total: shuffled.length, correct: 0, wrong: 0 });
    localStorage.removeItem(STORAGE_KEY);
  }

  function handleChoose(option) {
    if (wordResults[activeIndex]?.result !== 'none') return;

    const { correct } = words[activeIndex];
    const isCorrect = option === correct;

    const newResults = [...wordResults];
    newResults[activeIndex] = { result: isCorrect ? 'correct' : 'wrong', chosen: option };
    setWordResults(newResults);

    setStats(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      wrong: prev.wrong + (isCorrect ? 0 : 1),
    }));

    // Следующее неотвеченное после текущего, потом с начала
    let next = newResults.findIndex((r, i) => i > activeIndex && r.result === 'none');
    if (next === -1) next = newResults.findIndex(r => r.result === 'none');
    if (next !== -1) setActiveIndex(next);
  }

  function collectMistakes() {
    return words
      .map((entry, i) => ({ entry, result: wordResults[i]?.result }))
      .filter(item => item.result === 'wrong');
  }

  const accuracy = stats.total ? Math.round((stats.correct / stats.total) * 100) : 0;
  const isCurrentDone = wordResults[activeIndex]?.result !== 'none';

  return (
    <div className="trainer-container spelling-trainer-container">
      <div className="trainer-controls">
        <button onClick={reset} className="trainer-button">Сбросить</button>
        <button onClick={() => setShowMistakes(true)} className="trainer-button">Ошибки</button>
      </div>

      <div className="trainer-stats">
        Всего: <span>{stats.total}</span>,{' '}
        верно: <span style={{ color: 'green' }}>{stats.correct}</span>,{' '}
        ошибок: <span style={{ color: 'red' }}>{stats.wrong}</span>,{' '}
        точность: <span>{accuracy}%</span>
      </div>

      <main className="trainer-words">
        {words.map((entry, index) => (
          <SpellingItem
            key={index}
            ref={index === activeIndex ? activeRef : null}
            entry={entry}
            result={wordResults[index]}
            isActive={index === activeIndex}
            onClick={() => {
              if (wordResults[index]?.result === 'none') setActiveIndex(index);
            }}
          />
        ))}
      </main>

      <div className="spelling-keyboard">
        <button
          className={`spelling-key${isCurrentDone ? ' spelling-key--disabled' : ''}`}
          disabled={isCurrentDone}
          onClick={() => handleChoose('solid')}
        >
          Слитно
        </button>
        <button
          className={`spelling-key${isCurrentDone ? ' spelling-key--disabled' : ''}`}
          disabled={isCurrentDone}
          onClick={() => handleChoose('separate')}
        >
          Раздельно
        </button>
      </div>

      {showMistakes && (
        <SpellingMistakesPopup
          mistakes={collectMistakes()}
          onClose={() => setShowMistakes(false)}
        />
      )}
    </div>
  );
}

const SpellingItem = React.forwardRef(function SpellingItem(
  { entry, result, isActive, onClick }, ref
) {
  const { word, correct } = entry;
  const parts = parseParts(word);
  const done = result?.result !== 'none';

  let cls = 'spelling-item';
  if (isActive && !done) cls += ' spelling-item--active';
  if (done) cls += result.result === 'correct' ? ' spelling-item--correct' : ' spelling-item--wrong';

  return (
    <div ref={ref} className={cls} onClick={onClick}>
      <span className="spelling-word-text">
        {done
          ? resolveWord(word, correct)
          : parts.map((part, i) =>
              part.type === 'marker'
                ? <span key={i} className="spelling-gap">({part.value})</span>
                : <span key={i}>{part.value}</span>
            )
        }
      </span>
    </div>
  );
});


function SpellingMistakesPopup({ mistakes, onClose }) {
  return (
    <div className="trainer-popup-overlay" onClick={onClose}>
      <div className="trainer-popup" onClick={e => e.stopPropagation()}>
        <h2>Ошибки</h2>
        <div className="trainer-mistakes-list">
          {mistakes.length === 0 ? (
            <div>Ошибок нет! 🎉</div>
          ) : (
            mistakes.map(({ entry }, i) => (
              <div key={i} className="trainer-mistake-word">
                {resolveWord(entry.word, entry.correct)}
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
