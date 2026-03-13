import React, { useState, useRef, useEffect, useCallback } from "react";

export default function OptionSetsTab({ optionSets, options, onReload, registerAutoSave }) {
  const [selectedId,        setSelectedId]        = useState(null);
  const [nameDraft,         setNameDraft]         = useState("");
  const [selectedOptionIds, setSelectedOptionIds] = useState([]);
  const [isCreating,        setIsCreating]        = useState(false);

  const dirtyRef = useRef(false);
  const snapRef  = useRef({});
  useEffect(() => {
    snapRef.current = { selectedId, nameDraft, selectedOptionIds, isCreating };
  });

  const doSave = useCallback(async (snap) => {
    const { selectedId, nameDraft, selectedOptionIds, isCreating } = snap;
    if (!nameDraft.trim()) return;

    const body = { name: nameDraft.trim(), option_ids: selectedOptionIds };

    if (isCreating) {
      await fetch("/api/tasks/general/option-sets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setIsCreating(false);
    } else if (selectedId) {
      await fetch(`/api/tasks/general/option-sets/${selectedId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    await onReload();
  }, [onReload]);

  const autoSave = useCallback(async () => {
    if (!dirtyRef.current) return;
    dirtyRef.current = false;
    await doSave(snapRef.current);
  }, [doSave]);

  useEffect(() => { registerAutoSave(autoSave); });

  const handleSelect = async (id) => {
    await autoSave();
    const s = optionSets.find(x => x.id === id);
    setSelectedId(id);
    setIsCreating(false);
    setNameDraft(s?.name ?? "");
    setSelectedOptionIds((s?.options ?? []).map(o => o.id));
    dirtyRef.current = false;
  };

  const handleStartCreate = async () => {
    await autoSave();
    setSelectedId(null);
    setIsCreating(true);
    setNameDraft("");
    setSelectedOptionIds([]);
    dirtyRef.current = false;
  };

  const handleDelete = async () => {
    if (!selectedId || !window.confirm("Удалить набор?")) return;
    await fetch(`/api/tasks/general/option-sets/${selectedId}`, { method: "DELETE" });
    setSelectedId(null);
    setNameDraft("");
    setSelectedOptionIds([]);
    dirtyRef.current = false;
    await onReload();
  };

  const toggleOption = (id) => {
    setSelectedOptionIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
    dirtyRef.current = true;
  };

  return (
    <div className="form-main">
      {/* LEFT */}
      <div className="form-tree">
        <div className="form-tree__header">Наборы опций</div>
        <div className="form-tree__scroll">
          {optionSets.map(s => (
            <div
              key={s.id}
              className={selectedId === s.id
                ? "form-tree__item form-tree__item--active"
                : "form-tree__item"}
              onClick={() => handleSelect(s.id)}
            >
              <span className="form-tree__content">{s.name}</span>
              <span style={{ opacity: 0.4, fontSize: "0.78em", marginLeft: 6 }}>
                ({(s.options ?? []).length} опц.)
              </span>
            </div>
          ))}
          {isCreating && (
            <div className="form-tree__item form-tree__item--active">
              <em>Новый набор…</em>
            </div>
          )}
        </div>
        <button className="form-tree__add" onClick={handleStartCreate}>
          + Добавить набор
        </button>
      </div>

      {/* RIGHT */}
      <div className="form-editor">
        <div className="form-editor__header">
          {isCreating ? "Новый набор" : selectedId ? "Редактор набора" : "Выберите набор"}
        </div>
        {(selectedId || isCreating) && (
          <>
            <div className="form-editor__field">
              <label>Название</label>
              <input
                type="text"
                value={nameDraft}
                onChange={e => { setNameDraft(e.target.value); dirtyRef.current = true; }}
              />
            </div>

            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: "0.82rem", opacity: 0.65, marginBottom: 6 }}>
                Опции в наборе:
              </div>
              <div className="form-types-select">
                {options.map(o => (
                  <button
                    key={o.id}
                    type="button"
                    className={
                      selectedOptionIds.includes(o.id)
                        ? "form-types-select__chip form-types-select__chip--active"
                        : "form-types-select__chip"
                    }
                    onClick={() => toggleOption(o.id)}
                  >
                    {o.content}
                    {o.extras && (
                      <span style={{ opacity: 0.55, fontSize: "0.8em" }}> [{o.extras}]</span>
                    )}
                  </button>
                ))}
              </div>
              {selectedOptionIds.length > 0 && (
                <div style={{ fontSize: "0.78rem", opacity: 0.5, marginTop: 4 }}>
                  Выбрано: {selectedOptionIds.length}
                </div>
              )}
            </div>

            <div className="form-editor__actions">
              <button onClick={autoSave}>Сохранить</button>
              {selectedId && (
                <button className="form-editor__delete" onClick={handleDelete}>
                  Удалить
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
