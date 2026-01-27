import React from "react";

export function SubjectSelect({ subjects, selectedSubjectId, onChange }) {
  return (
    <div className="form-top__group">
      <label>Предмет:</label>
      <select
        value={selectedSubjectId || ""}
        onChange={(e) => {
          const v = e.target.value || null;
          onChange(v ? Number(v) : null);
        }}
      >
        <option value="">— выбери предмет —</option>
        {subjects.map((s) => (
          <option key={s.id} value={s.id}>
            {s.subject}
          </option>
        ))}
      </select>
    </div>
  );
}
