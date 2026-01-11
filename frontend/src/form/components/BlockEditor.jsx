import React from "react";

const BLOCK_TYPES = [
  { value: "title", label: "Заголовок" },
  { value: "subtitle", label: "Подзаголовок" },
  { value: "rule", label: "Правило" },
  { value: "example", label: "Пример" },
  { value: "exception", label: "Исключение" },
  { value: "important", label: "Важно" },
  { value: "text", label: "Текст" },
  { value: "svg", label: "Схема (SVG)" },
  { value: "group", label: "Группа (контейнер)" },
];

export function BlockEditor({
  selectedBlockId,
  blockDraft,
  setBlockDraft,
  canSave,
  onSaveBlock,
  onDeleteBlock,
}) {
  const handleChange = (field) => (e) => {
    setBlockDraft((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  return (
    <>
      {/* Заголовок редактора */}
      <div className="form-editor__field">
        <label style={{ minWidth: 0 }}>Блок</label>
      </div>

      {/* Тип и порядок в одной строке */}
      <div className="form-editor__field">
        <label>Тип</label>
        <select
          value={blockDraft.type}
          onChange={handleChange("type")}
          style={{ flex: 1 }}
        >
          {BLOCK_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        <label style={{ minWidth: 70, textAlign: "right" }}>Порядок</label>
        <input
          type="number"
          value={blockDraft.order}
          onChange={(e) =>
            setBlockDraft((prev) => ({
              ...prev,
              order: Number(e.target.value),
            }))
          }
          style={{ width: 80 }}
        />
      </div>

      {/* Подпись и содержимое на всю ширину */}
      <div className="form-editor__field">
        <label>Содержимое</label>
      </div>
      <div className="form-editor__field form-editor__field--textarea">
        <textarea
          value={blockDraft.content}
          onChange={handleChange("content")}
        />
      </div>

      <div className="form-editor__actions">
        <button onClick={onSaveBlock} disabled={!canSave}>
          Сохранить
        </button>
        <button
          className="form-editor__delete"
          onClick={onDeleteBlock}
          disabled={!selectedBlockId}
        >
          Удалить
        </button>
      </div>
    </>
  );
}
