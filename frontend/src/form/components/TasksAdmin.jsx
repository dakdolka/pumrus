import React, { useEffect, useState } from "react";

const TRAINER_TYPES = [
  { value: "stress",      label: "Орфоэпия (ударения)" },
  { value: "prefix",      label: "ПРЕ/ПРИ" },
  { value: "dictionary",  label: "Словарные слова" },
  { value: "spelling",    label: "Слитно / Раздельно" },
];

const INPUT_MODES = [
  { value: "letter_by_letter",  label: "Побуквенно" },
  { value: "whole_word_choice", label: "Выбор слова" },
  { value: "click_vowel",       label: "Клик по гласной" },
  { value: "keyboard",          label: "Клавиатура" },
];

const RAW_HINTS = {
  stress:     `["прИморье", "катАлог", "жалюзИ"]`,
  prefix:     `["прИрода", "прЕдел", "прИбой"]`,
  dictionary: `["кАлендарь", "кОридор"]`,
  spelling:   `[{"word": "в(течение) дня", "correct": "separate"}, {"word": "(по)тому", "correct": "solid"}]`,
};

export function TasksAdmin() {
  const [tasks,          setTasks]          = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const [nameDraft,    setNameDraft]    = useState("");
  const [trainerType,  setTrainerType]  = useState("stress");
  const [originalType, setOriginalType] = useState("stress"); // тип как в БД
  const [inputMode,    setInputMode]    = useState("letter_by_letter");
  const [isActive,     setIsActive]     = useState(true);
  const [rawText,      setRawText]      = useState("");
  const [parsedItems,  setParsedItems]  = useState([]);
  const [parseError,   setParseError]   = useState("");
  const [isCreating,   setIsCreating]   = useState(false);

  function reloadTasks() {
    fetch("/api/tasks/")
      .then((r) => r.json())
      .then(setTasks)
      .catch(console.error);
  }

  useEffect(() => {
    reloadTasks();
  }, []);

  useEffect(() => {
    if (!selectedTaskId) return;

    fetch(`/api/tasks/${selectedTaskId}`)
      .then((r) => r.json())
      .then((data) => {
        setNameDraft(data.name || "");
        setTrainerType(data.trainer_type || "stress");
        setOriginalType(data.trainer_type || "stress");
        setInputMode(data.input_mode || "letter_by_letter");
        setIsActive(data.is_active ?? true);
        setParsedItems(data.items || []);
        setParseError("");

        if (data.trainer_type === "spelling") {
          const raw = (data.items || []).map((it) => {
            try { return JSON.parse(it.raw); }
            catch { return it.raw; }
          });
          setRawText(JSON.stringify(raw, null, 2));
        } else {
          const raw    = (data.items || []).map((it) => it.raw);
          const unique = [...new Set(raw)];
          setRawText(JSON.stringify(unique, null, 2));
        }
      })
      .catch(console.error);
  }, [selectedTaskId]);

  function handleStartCreate() {
    setSelectedTaskId(null);
    setIsCreating(true);
    setNameDraft("");
    setTrainerType("stress");
    setOriginalType("stress");
    setInputMode("letter_by_letter");
    setIsActive(true);
    setRawText("");
    setParsedItems([]);
    setParseError("");
  }

  function handleSelectTask(id) {
    setIsCreating(false);
    setSelectedTaskId(id);
  }

  async function handleParseRaw() {
    setParseError("");
    let rawContent;
    try {
      rawContent = JSON.parse(rawText);
    } catch {
      setParseError("Ошибка: некорректный JSON в raw-массиве");
      return;
    }

    const res = await fetch("/api/tasks/parse-raw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trainer_type: trainerType, raw_content: rawContent }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setParseError(`Ошибка парсинга: ${err.detail || res.status}`);
      return;
    }

    const data = await res.json();
    setParsedItems(data.items || []);
  }

  async function handleCreate() {
    if (!nameDraft.trim()) {
      alert("Введите название задачи");
      return;
    }
    if (parsedItems.length === 0) {
      alert("Сначала сгенерируйте элементы (кнопка «Сгенерировать»)");
      return;
    }

    const created = await fetch("/api/tasks/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameDraft.trim(),
        trainer_type: trainerType,
        input_mode: inputMode,
        is_active: isActive,
      }),
    }).then((r) => r.json());

    await fetch(`/api/tasks/${created.id}/items`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsedItems),
    });

    reloadTasks();
    setIsCreating(false);
    setSelectedTaskId(created.id);
    setOriginalType(trainerType);
  }

  async function handleUpdate() {
    if (!selectedTaskId) return;

    await fetch(`/api/tasks/${selectedTaskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameDraft.trim(),
        trainer_type: trainerType,
        input_mode: inputMode,
        is_active: isActive,
      }),
    });

    if (parsedItems.length > 0) {
      // Есть свежесгенерированные items — сохраняем
      await fetch(`/api/tasks/${selectedTaskId}/items`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsedItems),
      });
      setOriginalType(trainerType);
    } else if (trainerType !== originalType) {
      // Тип сменили, но новый raw не сгенерировали — предупреждаем
      alert(
        `Тип тренажёра изменён с «${originalType}» на «${trainerType}», ` +
        `но элементы не обновлены.\n\n` +
        `Вставьте новый raw-массив и нажмите «Сгенерировать» — иначе тренажёр сломается.`
      );
      reloadTasks();
      return;
    }
    // Если тип не менялся и items не трогали — просто сохраняем мета-поля, всё ок

    reloadTasks();
  }

  async function handleDelete() {
    if (!selectedTaskId) return;
    if (!window.confirm("Удалить задачу?")) return;

    await fetch(`/api/tasks/${selectedTaskId}`, { method: "DELETE" });

    setSelectedTaskId(null);
    setIsCreating(false);
    setNameDraft("");
    setParsedItems([]);
    setRawText("");
    reloadTasks();
  }

  const isEditing     = !!selectedTaskId || isCreating;
  const typeChanged   = !isCreating && trainerType !== originalType;

  return (
    <div className="form-main">
      {/* ЛЕВАЯ ЧАСТЬ: список задач */}
      <div className="form-tree">
        <div className="form-tree__header">Задания (тренажёры)</div>
        <div className="form-tree__scroll">
          {tasks.map((t) => (
            <div
              key={t.id}
              className={
                selectedTaskId === t.id
                  ? "form-tree__item form-tree__item--active"
                  : "form-tree__item"
              }
              onClick={() => handleSelectTask(t.id)}
            >
              <span style={{ marginRight: 6, opacity: 0.5, fontSize: "0.8em" }}>
                [{t.trainer_type}]
              </span>
              {t.name}
              {!t.is_active && (
                <span style={{ marginLeft: 6, opacity: 0.4, fontSize: "0.8em" }}>
                  (неакт.)
                </span>
              )}
            </div>
          ))}
        </div>
        <button className="form-tree__add" onClick={handleStartCreate}>
          + Добавить задание
        </button>
      </div>

      {/* ПРАВАЯ ЧАСТЬ: редактор */}
      <div
        className="form-editor"
        style={{ display: "flex", flexDirection: "column", minHeight: 0 }}
      >
        <div className="form-editor__header">
          {isCreating
            ? "Новое задание"
            : selectedTaskId
            ? "Редактор задания"
            : "Выберите задание"}
        </div>

        {isEditing && (
          <>
            {/* Название */}
            <div className="form-editor__field">
              <label>Название</label>
              <input
                type="text"
                value={nameDraft}
                onChange={(e) => setNameDraft(e.target.value)}
              />
            </div>

            {/* Тип тренажёра */}
            <div className="form-editor__field">
              <label>Тип тренажёра</label>
              <select
                value={trainerType}
                onChange={(e) => {
                  setTrainerType(e.target.value);
                  setParsedItems([]);
                  setRawText("");
                  setParseError("");
                }}
              >
                {TRAINER_TYPES.map((tt) => (
                  <option key={tt.value} value={tt.value}>
                    {tt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Предупреждение о смене типа */}
            {typeChanged && (
              <div style={{
                color: "#f0a500",
                fontSize: "0.82rem",
                marginBottom: 6,
                padding: "5px 8px",
                borderRadius: 6,
                background: "rgba(240,165,0,0.08)",
                border: "1px solid rgba(240,165,0,0.25)",
              }}>
                ⚠️ Тип изменён — обновите raw-массив и нажмите «Сгенерировать»
              </div>
            )}

            {/* Режим ввода */}
            <div className="form-editor__field">
              <label>Режим ввода</label>
              <select
                value={inputMode}
                onChange={(e) => setInputMode(e.target.value)}
              >
                {INPUT_MODES.map((im) => (
                  <option key={im.value} value={im.value}>
                    {im.label}
                  </option>
                ))}
              </select>
            </div>

            {/* is_active */}
            <div
              className="form-editor__field"
              style={{ flexDirection: "row", alignItems: "center", gap: 8 }}
            >
              <label style={{ margin: 0 }}>Активно</label>
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
            </div>

            {/* Raw-контент */}
            <div
              className="form-editor__field"
              style={{ flexDirection: "column", alignItems: "stretch" }}
            >
              <label>
                Raw-массив
                <span className="field-hint">
                  Пример: {RAW_HINTS[trainerType]}
                </span>
              </label>
              <textarea
                value={rawText}
                onChange={(e) => {
                  setRawText(e.target.value);
                  setParsedItems([]);
                  setParseError("");
                }}
                rows={6}
                placeholder={RAW_HINTS[trainerType]}
              />
            </div>

            {parseError && (
              <div style={{ color: "#ff6b6b", fontSize: "0.85rem", marginBottom: 8 }}>
                {parseError}
              </div>
            )}

            <div className="form-editor__actions">
              <button type="button" onClick={handleParseRaw}>
                Сгенерировать элементы
              </button>
            </div>

            {/* Предпросмотр элементов */}
            {parsedItems.length > 0 && (
              <div
                style={{
                  flex: "1 1 auto",
                  minHeight: 0,
                  overflowY: "auto",
                  marginTop: 12,
                  border: "1px solid var(--block-color)",
                  borderRadius: 6,
                  padding: 8,
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 6, fontSize: "0.9rem" }}>
                  Элементов: {parsedItems.length}
                </div>
                <table style={{ width: "100%", fontSize: "0.82rem", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ opacity: 0.6 }}>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>#</th>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>raw</th>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>visible</th>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>correct</th>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>correct_visible</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedItems.map((item, idx) => (
                      <tr key={idx} style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}>
                        <td style={{ padding: "3px 6px 3px 0" }}>{idx + 1}</td>
                        <td style={{ padding: "3px 6px" }}>{item.raw}</td>
                        <td style={{ padding: "3px 6px" }}>{item.visible}</td>
                        <td style={{ padding: "3px 6px", fontWeight: 600 }}>{item.correct_option}</td>
                        <td style={{ padding: "3px 6px" }}>{item.correct_visible}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="form-editor__actions" style={{ marginTop: 12 }}>
              {isCreating ? (
                <button type="button" onClick={handleCreate}>
                  Создать задание
                </button>
              ) : (
                <>
                  <button type="button" onClick={handleUpdate}>
                    Сохранить изменения
                  </button>
                  <button
                    type="button"
                    className="form-editor__delete"
                    onClick={handleDelete}
                  >
                    Удалить задание
                  </button>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
