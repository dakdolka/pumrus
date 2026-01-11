import React from "react";

export function TheoryTypeSelect({
  availableTypes,
  selectedTypeIds,
  onChange,
  disabled,
}) {
  const handleChange = (e) => {
    const options = Array.from(e.target.selectedOptions);
    const ids = options.map((o) => Number(o.value));
    onChange(ids);
  };

  return (
    <div className="form-top__group">
      <label>Типы:</label>
      <select
        multiple
        value={selectedTypeIds}
        onChange={handleChange}
        disabled={disabled}
        style={{ minHeight: 60 }}
      >
        {availableTypes.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
    </div>
  );
}
