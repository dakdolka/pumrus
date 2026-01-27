import React from "react";

export function TheoryTypeSelect({
  availableTypes,
  selectedTypeIds,
  onChange,
  disabled,
}) {
  const toggleType = (id) => {
    if (disabled) return;
    const isSelected = selectedTypeIds.includes(id);
    const next = isSelected
      ? selectedTypeIds.filter((x) => x !== id)
      : [...selectedTypeIds, id];
    onChange(next);
  };

  if (!availableTypes || availableTypes.length === 0) {
    return null;
  }

  return (
    <div className="form-top__group">
      <label>Типы:</label>
      <div className="form-types-select">
        {availableTypes.map((t) => {
          const active = selectedTypeIds.includes(t.id);
          const className = [
            "form-types-select__chip",
            active ? "form-types-select__chip--active" : "",
            disabled ? "form-types-select__chip--disabled" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <div
              key={t.id}
              className={className}
              onClick={() => toggleType(t.id)}
            >
              {t.name}
            </div>
          );
        })}
      </div>
    </div>
  );
}
