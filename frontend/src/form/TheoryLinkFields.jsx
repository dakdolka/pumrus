import FormattedText from "./FormattedText";
import { theoryHref } from "../theory/theoryLinks";

export default function TheoryLinkFields({ data, setData, catalog }) {
  const topics = (catalog?.tasks || []).flatMap((task) => task.topics.map((topic) => ({...topic, taskNumber:task.number})));
  const href = theoryHref(data);
  return <div className="field-stack">
    <FormattedText label="Текст продолжения теории" value={data.markdown || ""} onChange={(markdown) => setData({markdown})} compact />
    <label>Тема продолжения<select value={data.topicId || ""} onChange={(event) => {
      const topic = topics.find((item) => item.id === Number(event.target.value));
      setData({topicId:topic?.id || null, taskNumber:topic?.taskNumber || null, anchor:""});
    }}><option value="">Выберите тему</option>{topics.map((topic) => <option key={`${topic.taskNumber}:${topic.id}`} value={topic.id}>Задание {topic.taskNumber} · {topic.title}{topic.status === "hidden" ? " · скрыта" : ""}</option>)}</select></label>
    <label>Раздел в теме · необязательно<input value={data.anchor || ""} onChange={(event) => setData({anchor:event.target.value})} placeholder="Например: i-y-suffix" /></label>
    <small>Метка раздела задаётся у нужного блока в поле «Метка для ссылки». Используйте латинские буквы, цифры и дефис.</small>
    <label>Текст кнопки<input value={data.buttonLabel || ""} onChange={(event) => setData({buttonLabel:event.target.value})} placeholder="Продолжить тему" /></label>
    <small>{href || "Выберите тему и проверьте метку раздела."}</small>
  </div>;
}
