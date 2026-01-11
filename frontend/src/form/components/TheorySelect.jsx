import React from "react";

export function TheorySelect({
  theories,
  selectedTheoryId,
  onChange,
  onCreate,
  disabled,
}) {
  return (
    <div className="form-top__group">
      <label>Теория:</label>
      <select
        value={selectedTheoryId || ""}
        onChange={(e) => {
          const v = e.target.value || null;
          onChange(v ? Number(v) : null);
        }}
        disabled={disabled}
      >
        <option value="">— выбери теорию —</option>
        {theories.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      <button onClick={onCreate} disabled={disabled}>
        Создать новую теорию
      </button>
    </div>
  );
}
