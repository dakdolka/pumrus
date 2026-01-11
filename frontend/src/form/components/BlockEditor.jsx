import React, { useRef } from "react";

const BLOCK_TYPES = [
  { value: "title", label: "Заголовок" },
  { value: "subtitle", label: "Подзаголовок" },
  { value: "rule", label: "Правило" },
  { value: "example", label: "Пример" },
  { value: "exception", label: "Исключение" },
  { value: "important", label: "Важно" },
  { value: "text", label: "Текст" },
  { value: "svg", label: "Svg" },
  { value: "group", label: "Группа" },
];

export function BlockEditor({
  selectedBlockId,
  blockDraft,
  setBlockDraft,
  canSave,
  onSaveBlock,
  onDeleteBlock,
}) {
  const textareaRef = useRef(null);

  const handleChange = (field) => (e) => {
    setBlockDraft((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  const handleTypeClick = (value) => {
    setBlockDraft((prev) => ({
      ...prev,
      type: value,
    }));
  };

  const handleBoldClick = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const value = blockDraft.content ?? "";
    const start = textarea.selectionStart ?? 0;
    const end = textarea.selectionEnd ?? 0;

    if (start === end) return;

    const before = value.slice(0, start);
    const selected = value.slice(start, end);
    const after = value.slice(end);

    const hasBold =
      selected.startsWith("**") &&
      selected.endsWith("**") &&
      selected.length > 4;

    let newSelected;
    if (hasBold) {
      newSelected = selected.slice(2, selected.length - 2);
    } else {
      newSelected = `**${selected}**`;
    }

    const newValue = before + newSelected + after;

    setBlockDraft((prev) => ({
      ...prev,
      content: newValue,
    }));

    const delta = newSelected.length - selected.length;
    const newEnd = end + delta;
    requestAnimationFrame(() => {
      textarea.selectionStart = start;
      textarea.selectionEnd = newEnd;
      textarea.focus();
    });
  };

  if (!selectedBlockId) {
    return (
      <div style={{ opacity: 0.7, fontSize: "0.9rem" }}>
        Выберите блок в дереве слева, чтобы редактировать
      </div>
    );
  }

  return (
    <>
      <div className="form-editor__field">
        <div className="form-types-select">
          {BLOCK_TYPES.map((t) => {
            const active = blockDraft.type === t.value;
            const className = [
              "form-types-select__chip",
              active ? "form-types-select__chip--active" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <div
                key={t.value}
                className={className}
                onClick={() => handleTypeClick(t.value)}
              >
                {t.label}
              </div>
            );
          })}
        </div>
      </div>

      <div className="form-editor__field">
        <button
          type="button"
          className="form-editor__bold-btn"
          onClick={handleBoldClick}
        >
          Bold
        </button>
      </div>

      <div className="form-editor__field form-editor__field--textarea">
        <textarea
          ref={textareaRef}
          value={blockDraft.content ?? ""}
          onChange={handleChange("content")}
        />
      </div>

      <div className="form-editor__actions">
        <button
          type="button"
          onClick={onSaveBlock}
          disabled={!canSave}
        >
          Сохранить блок
        </button>
        <button
          type="button"
          className="form-editor__delete"
          onClick={onDeleteBlock}
          disabled={!canSave}
        >
          Удалить блок
        </button>
      </div>
    </>
  );
}
