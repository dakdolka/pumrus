import React from "react";

export function BlockEditor({
  selectedBlockId,
  blockDraft,
  setBlockDraft,
  canCreate,
  canSave,
  onCreateBlock,
  onSaveBlock,
  onDeleteBlock,
}) {
  return (
    <div className="form-editor">
      <div className="form-editor__header">
        Редактор блока {selectedBlockId ? `#${selectedBlockId}` : "(новый)"}
      </div>

      <div className="form-editor__field">
        <label>Тип:</label>
        <input
          type="text"
          value={blockDraft.type}
          onChange={(e) =>
            setBlockDraft((prev) => ({ ...prev, type: e.target.value }))
          }
        />
      </div>

      <div className="form-editor__field">
        <label>Parent ID:</label>
        <input
          type="number"
          value={blockDraft.parent_id ?? ""}
          onChange={(e) =>
            setBlockDraft((prev) => ({
              ...prev,
              parent_id: e.target.value ? Number(e.target.value) : null,
            }))
          }
        />
      </div>

      <div className="form-editor__field">
        <label>Order:</label>
        <input
          type="number"
          value={blockDraft.order}
          onChange={(e) =>
            setBlockDraft((prev) => ({
              ...prev,
              order: Number(e.target.value) || 0,
            }))
          }
        />
      </div>

      <div className="form-editor__field form-editor__field--textarea">
        <label>Markdown:</label>
        <textarea
          value={blockDraft.content}
          onChange={(e) =>
            setBlockDraft((prev) => ({ ...prev, content: e.target.value }))
          }
        />
      </div>

      <div className="form-editor__actions">
        <button onClick={onCreateBlock} disabled={!canCreate}>
          Сохранить как новый блок
        </button>
        <button onClick={onSaveBlock} disabled={!canSave}>
          Сохранить изменения блока
        </button>
        <button
          onClick={onDeleteBlock}
          disabled={!canSave}
          className="form-editor__delete"
        >
          Удалить блок
        </button>
      </div>
    </div>
  );
}
