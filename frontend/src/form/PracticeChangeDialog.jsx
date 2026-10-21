import { useEffect, useMemo, useRef, useState } from "react";
import { Markdown } from "../theory/TheoryRenderer";
import "./practiceChanges.css";

function legacyWord(version) {
  const answer=String(version.feedbackData?.correctAnswer || "").toLocaleLowerCase("ru");
  const index=String(version.promptData?.content || "").indexOf("_");
  const match=[...answer.matchAll(/[а-яё]+(?:-[а-яё]+)*/g)].find(item=>item.index<=index && item.index+item[0].length>index);
  return (match?.[0] || answer).replace("ё","е");
}

export default function PracticeChangeDialog({ api, onClose, onApplied, localDirty }) {
  const dialog = useRef(null);
  const [source, setSource] = useState("");
  const [approvedSource, setApprovedSource] = useState("");
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [topicCode, setTopicCode] = useState("");
  const [page, setPage] = useState(0);
  const parsed = useMemo(() => {
    if (!source.trim()) return {value:null,error:""};
    try {
      if (source.length > 8_000_000) throw Error("Пакет больше 8 МБ");
      const value=JSON.parse(source.trim().replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/i,"$1"));
      if (value.format!=="pumrus.practice-edit" || value.schemaVersion!==1 || !Array.isArray(value.after?.topics) || ["versions","sets","memberships"].some(key=>!Array.isArray(value.before?.[key]))) throw Error("Ожидается пакет pumrus.practice-edit, версия 1");
      for (const topic of value.after.topics) {
        if (typeof topic?.title!=="string" || typeof topic.topicCode!=="string" || !Array.isArray(topic.cards)) throw Error("В каждой теме должны быть название, topicCode и массив cards");
        for (const card of topic.cards) {
          if (["prompt","answer","lexeme","explanation","curated_key"].some(key=>typeof card?.[key]!=="string") || !Array.isArray(card.source_references)) throw Error("В карточке ожидаются текстовые prompt, answer, lexeme, explanation и curated_key, а также список source_references");
          for (const source of card.source_references) { if (typeof source!=="string" || new URL(source).protocol!=="https:") throw Error("Источник карточки должен быть корректной HTTPS-ссылкой"); }
        }
      }
      if (value.before.versions.some(version=>version.promptData?.content!=null && typeof version.promptData.content!=="string")) throw Error("В before повреждён текст карточки. Верните исходную выгрузку.");
      return {value,error:""};
    } catch(reason) {return {value:null,error:reason.message};}
  },[source]);
  const value=parsed.value;
  const cards=useMemo(()=>value?.after.topics.flatMap(topic=>topic.cards.map(card=>({...card,topicTitle:topic.title}))) || [],[value]);
  const filtered=cards.filter(card=>(!topicCode || card.topic_code===topicCode) && `${card.lexeme} ${card.explanation}`.toLocaleLowerCase("ru").includes(query.toLocaleLowerCase("ru")));
  const shown=filtered.slice(page*30,(page+1)*30);
  const beforeCards=value?.before.versions || [];
  const beforeByWord=new Map(beforeCards.map(version=>[legacyWord(version),version]));
  const afterWords=new Set(cards.map(card=>card.lexeme.replace("ё","е")));
  const omitted=[...beforeByWord.keys()].filter(word=>!afterWords.has(word));
  useEffect(()=>{dialog.current.showModal();const previous=document.body.style.overflow;document.body.style.overflow="hidden";return()=>{document.body.style.overflow=previous;};},[]);
  function close() {
    if (!busy && (!source || window.confirm("Закрыть предпросмотр? Сохраните JSON, если изменяли его."))) onClose();
  }
  async function check() {
    if (!value) return;
    setBusy(true);setError("");setReport(null);setApprovedSource("");
    try {const response=await api("/practice-edit/preview",{method:"POST",body:JSON.stringify(value)});setReport(response);setApprovedSource(source);}
    catch(reason){setError(reason.message);}finally{setBusy(false);}
  }
  async function apply() {
    if (!value || source!==approvedSource || !report || busy || localDirty) return;
    setBusy(true);setError("");
    try {const response=await api("/practice-edit/apply",{method:"POST",body:JSON.stringify(value)});onApplied(response);}
    catch(reason){setError(reason.message);setApprovedSource("");}finally{setBusy(false);}
  }
  function save() {
    const url=URL.createObjectURL(new Blob([source],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download="pumrus-practice-edit.json";link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <dialog ref={dialog} className="practice-change-dialog" aria-labelledby="practice-change-title" onCancel={event=>{event.preventDefault();close();}}>
    <header><div><span className="overline">Задания 10 и 11</span><h2 id="practice-change-title">Обновление банка практики</h2></div><button className="button" disabled={busy} onClick={close}>Закрыть</button></header>
    <div className="practice-change-body">
      <p>Вставьте подготовленный JSON. Сначала проверьте слова, объяснения и темы, затем примените банк целиком. Совпадающие упражнения сохранят свои номера и историю.</p>
      <div className="practice-change-actions"><label className="button">Открыть JSON<input hidden disabled={busy} type="file" accept=".json,application/json" onChange={async event=>{const file=event.target.files?.[0];event.target.value="";if(!file)return;setSource(await file.text());setApprovedSource("");setReport(null);setError("");setPage(0);}} /></label><button className="button" disabled={!source || busy} onClick={save}>Сохранить JSON</button></div>
      <label>Код изменений · JSON<textarea className="practice-change-source" value={source} disabled={busy} spellCheck={false} onChange={event=>{setSource(event.target.value);setReport(null);setApprovedSource("");setError("");setPage(0);}} /></label>
      {(parsed.error || error) && <p className="form-error" role="alert">{parsed.error || error}</p>}
      {localDirty && <p className="form-error">Сначала сохраните изменения настроек подборок в основной форме.</p>}
      {value && <>
        <div className="practice-change-totals"><article><span>До</span><strong>{beforeCards.length}</strong><small>упражнений · без пояснений: {beforeCards.filter(v=>!v.feedbackData?.correct).length}</small></article><article><span>После</span><strong>{cards.length}</strong><small>карточек · {value.after.topics.length} тем · со ссылками на источники</small></article></div>
        <div className="practice-change-topics"><table><thead><tr><th>Тема</th><th>До</th><th>После</th></tr></thead><tbody>{value.after.topics.map(topic=><tr key={topic.topicId}><th>{topic.taskNumber} · {topic.title}</th><td>{value.before.sets.find(set=>set.topicId===topic.topicId)?.id ? value.before.memberships.filter(m=>m.exerciseSetId===value.before.sets.find(set=>set.topicId===topic.topicId).id).length : "—"}</td><td>{topic.cards.length}</td></tr>)}</tbody></table></div>
        {omitted.length>0 && <details><summary>Не входят в новый банк · {omitted.length}</summary><p>Эти слова или формы убираются из активных наборов. Их история сохраняется в архиве. Проверьте список перед применением.</p><p>{omitted.join(", ")}</p></details>}
        <div className="practice-change-filters"><label>Тема<select aria-label="Тема" value={topicCode} onChange={event=>{setTopicCode(event.target.value);setPage(0);}}><option value="">Все темы</option>{value.after.topics.map(topic=><option key={topic.topicId} value={topic.topicCode}>{topic.taskNumber} · {topic.title}</option>)}</select></label><label>Слово или правило<input value={query} onChange={event=>{setQuery(event.target.value);setPage(0);}} /></label></div>
        <div className="practice-change-cards">{shown.map(card=>{
          const before=beforeByWord.get(card.lexeme.replace("ё","е"));
          return <article key={card.curated_key}><header><small>{card.topicTitle}</small><strong>{card.prompt}</strong></header><div className="practice-card-comparison"><section><span>До</span>{before ? <><p>{before.promptData?.content}</p><Markdown value={before.feedbackData?.correct || "Пояснение отсутствует"} /></> : <p>Новое слово в банке</p>}</section><section><span>После</span><p className="practice-card-answer">{card.answer}</p><Markdown value={card.explanation} /><details><summary>Проверенные источники</summary><ul>{(card.source_references || []).filter(url=>/^https:\/\//.test(url)).map(url=><li key={url}><a href={url} target="_blank" rel="noreferrer">{new URL(url).hostname}{url.startsWith("https://orfo.ruslang.ru/search/word?") ? " · словарная запись" : " · правило"}</a></li>)}</ul></details></section></div></article>;
        })}</div>
        <div className="practice-change-pagination"><button className="button" disabled={page===0} onClick={()=>setPage(page-1)}>← Назад</button><span>{filtered.length ? page*30+1 : 0}–{Math.min((page+1)*30,filtered.length)} из {filtered.length}</span><button className="button" disabled={(page+1)*30>=filtered.length} onClick={()=>setPage(page+1)}>Далее →</button></div>
      </>}
      {report && <p className="form-notice" role="status">Пакет проверен на сервере: исходная версия совпадает, слова и привязки корректны. Можно применять.</p>}
    </div>
    <footer><button className="button" disabled={!value || busy} onClick={check}>{busy ? "Обрабатываем…" : "Проверить пакет"}</button><button className="button primary" disabled={!value || !report || source!==approvedSource || busy || localDirty} onClick={apply}>Применить изменения</button></footer>
  </dialog>;
}
