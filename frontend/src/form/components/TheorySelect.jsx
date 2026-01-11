import React from "react";

export function TheorySelect({
  theories,
  selectedTheoryId,
  onChange,
  disabled,
}) {
  const handleChange = (e) => {
    const value = e.target.value;
    onChange(value ? Number(value) : null);
  };

  return (
    <select
      value={selectedTheoryId ?? ""}
      onChange={handleChange}
      disabled={disabled}
    >
      <option value="">Выберите теорию</option>
      {theories.map((t) => (
        <option key={t.id} value={t.id}>
          {t.name}
        </option>
      ))}
    </select>
  );
}
