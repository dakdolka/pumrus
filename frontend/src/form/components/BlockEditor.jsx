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
  { value: "link", label: "Ссылка"}
];

export function BlockEditor({ block, onChange, disabled }) {
  const textareaRef = useRef(null);
  const canEdit = !disabled && !!block;

  // Простой handleChange - НЕ конвертируем, храним реальные переносы
  const handleChange = (field) => (e) => {
    if (!canEdit) return;
    onChange((prev) => ({
      ...prev,
      [field]: e.target.value, // Храним как есть с реальными \n
    }));
  };

  const handleTypeClick = (value) => {
    if (!canEdit) return;
    onChange((prev) => ({
      ...prev,
      type: value,
    }));
  };

  const handleBoldClick = () => {
    if (!canEdit) return;
    const textarea = textareaRef.current;
    if (!textarea) return;

    const value = block?.content ?? "";
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

    onChange((prev) => ({
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

  if (!block) {
    return (
      <div style={{ opacity: 0.6 }}>
        Выберите блок в дереве слева, чтобы отредактировать.
      </div>
    );
  }

  return (
    <>
      <div
        className="form-editor__field"
        style={{ alignItems: "flex-start", marginBottom: 4 }}
      >
        <div className="form-types-select">
          {BLOCK_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              className={
                block.type === t.value
                  ? "form-types-select__chip form-types-select__chip--active"
                  : "form-types-select__chip"
              }
              onClick={() => handleTypeClick(t.value)}
              disabled={disabled}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="form-editor__field" style={{ marginBottom: 8 }}>
        <button
          type="button"
          className="form-editor__bold-btn"
          onClick={handleBoldClick}
          disabled={disabled}
        >
          Bold
        </button>
      </div>

      <div className="form-editor__field form-editor__field--textarea">
        <textarea
          ref={textareaRef}
          value={block.content ?? ""}
          onChange={handleChange("content")}
          disabled={disabled}
        />
      </div>
    </>
  );
}
