import React, { useEffect, useState } from "react";
import "./form.css";

import { TheorySelect }      from "./components/TheorySelect";
import { BlocksTree }        from "./components/BlocksTree";
import { BlockEditor }       from "./components/BlockEditor";
import { TheoryTypeSelect }  from "./components/TheoryTypeSelect";
import { TasksTheoryEditor } from "./components/TasksTheoryEditor";
import { TasksAdmin }        from "./components/tasks/TasksAdmin";  // ← новый

function FormApp() {
  const [theoryTypes, setTheoryTypes] = useState([]);
  const [theories, setTheories] = useState([]);
  const [selectedTheoryId, setSelectedTheoryId] = useState(null);
  const [theory, setTheory] = useState(null);

  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [blockDraft, setBlockDraft] = useState({
    type: "text",
    content: "",
    parent_id: null,
    order: 0,
  });

  const [selectedTheoryTypeIds, setSelectedTheoryTypeIds] = useState([]);
  const [isCreatingTheory, setIsCreatingTheory] = useState(false);
  const [newTheoryName, setNewTheoryName] = useState("");

  const [activeTab, setActiveTab] = useState("theory"); // "theory" | "tasks" | "trainers"

  const availableTheoryTypes = theoryTypes;

  function resetTheoryState() {
    setSelectedTheoryId(null);
    setTheory(null);
    setSelectedBlockId(null);
    setBlockDraft({ type: "text", content: "", parent_id: null, order: 0 });
    setSelectedTheoryTypeIds([]);
    setIsCreatingTheory(false);
    setNewTheoryName("");
  }

  function convertBlocksFromAPI(blocks) {
    return blocks.map((block) => {
      const converted = {
        ...block,
        content: (block.content || "").replace(/\\n/g, "\n"),
      };
      if (block.children && block.children.length > 0) {
        converted.children = convertBlocksFromAPI(block.children);
      }
      return converted;
    });
  }

  function convertBlockForAPI(block) {
    return {
      ...block,
      content: (block.content || "").replace(/\n/g, "\\n"),
    };
  }

  function flattenBlocks(nodes) {
    if (!Array.isArray(nodes)) return [];
    const res = [];
    const walk = (arr) => {
      arr.forEach((n) => {
        res.push(n);
        if (Array.isArray(n.children) && n.children.length) walk(n.children);
      });
    };
    walk(nodes);
    return res;
  }

  function collectAllChildIds(blocks) {
    const ids = new Set();
    const walk = (nodes) => {
      if (!Array.isArray(nodes)) return;
      nodes.forEach((n) => {
        if (Array.isArray(n.children) && n.children.length) {
          n.children.forEach((ch) => ids.add(ch.id));
          walk(n.children);
        }
      });
    };
    walk(blocks || []);
    return ids;
  }

  function collectChildrenForParent(blocks, parentId) {
    if (parentId == null) {
      const childIds = collectAllChildIds(blocks);
      return (blocks || []).filter((b) => !childIds.has(b.id));
    }
    const res = [];
    const walk = (nodes) => {
      if (!Array.isArray(nodes)) return;
      nodes.forEach((n) => {
        if (n.id === parentId) {
          if (Array.isArray(n.children)) res.push(...n.children);
        } else if (Array.isArray(n.children) && n.children.length) {
          walk(n.children);
        }
      });
    };
    walk(blocks || []);
    return res;
  }

  async function createBlockAt(theoryId, parentId) {
    const blocks = theory?.blocks || [];
    const siblings = collectChildrenForParent(blocks, parentId);
    let order = 0;
    if (siblings.length > 0) {
      const sorted = [...siblings].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
      order = (sorted[sorted.length - 1].order ?? 0) + 1;
    }

    await fetch(`/api/theory/${theoryId}/blocks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "text", content: "", parent_id: parentId, order }),
    });

    const updatedTheory = await fetch(`/api/theory/get_theory/${theoryId}`).then((r) => r.json());
    if (updatedTheory.blocks) updatedTheory.blocks = convertBlocksFromAPI(updatedTheory.blocks);

    const flat = flattenBlocks(updatedTheory.blocks || []);
    if (flat.length > 0) {
      const maxIdBlock = flat.reduce((acc, b) => (!acc || b.id > acc.id ? b : acc), null);
      if (maxIdBlock) setSelectedBlockId(maxIdBlock.id);
    }
    return updatedTheory;
  }

  useEffect(() => {
    fetch("/api/theory/all_theory_types")
      .then((r) => r.json())
      .then(setTheoryTypes)
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetch(`/api/theory/all_theory`)
      .then((r) => r.json())
      .then((data) => {
        setTheories(data);
        if (selectedTheoryId) {
          const t = data.find((th) => th.id === selectedTheoryId);
          setSelectedTheoryTypeIds(
            t && Array.isArray(t.types) ? t.types.map((tt) => tt.id) : []
          );
        } else {
          setSelectedTheoryTypeIds([]);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedTheoryId) return;
    const t = theories.find((th) => th.id === selectedTheoryId);
    setSelectedTheoryTypeIds(
      t && Array.isArray(t.types) ? t.types.map((tt) => tt.id) : []
    );

    fetch(`/api/theory/get_theory/${selectedTheoryId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.blocks) data.blocks = convertBlocksFromAPI(data.blocks);
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({ type: "text", content: "", parent_id: null, order: 0 });
      })
      .catch(console.error);
  }, [selectedTheoryId, theories]);

  useEffect(() => {
    if (!theory || !selectedBlockId) return;
    const block = flattenBlocks(theory.blocks || []).find((b) => b.id === selectedBlockId);
    if (!block) return;
    setBlockDraft({ type: block.type, content: block.content, parent_id: null, order: block.order ?? 0 });
  }, [selectedBlockId, theory]);

  function handleStartCreateTheory() {
    resetTheoryState();
    setIsCreatingTheory(true);
  }

  function handleSaveNewTheory() {
    if (!newTheoryName.trim()) return;
    fetch("/api/theory/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newTheoryName.trim(), type_ids: selectedTheoryTypeIds }),
    })
      .then((r) => r.json())
      .then((data) => {
        const typesForNewTheory = availableTheoryTypes.filter((t) =>
          selectedTheoryTypeIds.includes(t.id)
        );
        setTheories((prev) => [...prev, { id: data.id, name: data.name, types: typesForNewTheory }]);
        setSelectedTheoryId(data.id);
        setTheory(data);
        setIsCreatingTheory(false);
        setNewTheoryName("");
      })
      .catch(console.error);
  }

  function handleUpdateTheoryTypes(newTypeIds) {
    setSelectedTheoryTypeIds(newTypeIds);
    if (!selectedTheoryId) return;
    fetch(`/api/theory/${selectedTheoryId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type_ids: newTypeIds }),
    })
      .then((r) => r.json())
      .then((data) => {
        setTheory(data);
        const newTypes = availableTheoryTypes.filter((t) => newTypeIds.includes(t.id));
        setTheories((prev) =>
          prev.map((th) => (th.id === selectedTheoryId ? { ...th, types: newTypes } : th))
        );
      })
      .catch(console.error);
  }

  function handleSaveBlock() {
    if (!selectedBlockId) return;
    const blockToSave = convertBlockForAPI(blockDraft);
    fetch(`/api/theory/blocks/${selectedBlockId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(blockToSave),
    })
      .then(() => fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) => r.json()))
      .then((data) => {
        if (data.blocks) data.blocks = convertBlocksFromAPI(data.blocks);
        setTheory(data);
      })
      .catch(console.error);
  }

  function handleDeleteBlock() {
    if (!selectedBlockId) return;
    if (!window.confirm("Удалить блок?")) return;
    fetch(`/api/theory/blocks/${selectedBlockId}`, { method: "DELETE" })
      .then(() => fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) => r.json()))
      .then((data) => {
        if (data.blocks) data.blocks = convertBlocksFromAPI(data.blocks);
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({ type: "text", content: "", parent_id: null, order: 0 });
      })
      .catch(console.error);
  }

  const canSaveBlock = !!selectedBlockId;

  function handleMoveBlock(blockId, direction) {
    if (!theory || !Array.isArray(theory.blocks)) return;
    const allBlocks = flattenBlocks(theory.blocks || []);
    const target = allBlocks.find((b) => b.id === blockId);
    if (!target) return;
    const siblings = collectChildrenForParent(theory.blocks || [], target.parent_id);
    if (!siblings.length) return;
    const sorted = [...siblings].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    const index = sorted.findIndex((b) => b.id === blockId);
    if (index === -1) return;
    let swapWith = null;
    if (direction === "up" && index > 0) swapWith = sorted[index - 1];
    else if (direction === "down" && index < sorted.length - 1) swapWith = sorted[index + 1];
    if (!swapWith) return;
    const newOrder = target.order ?? 0;
    const swapOrder = swapWith.order ?? 0;
    target.order = swapOrder;
    swapWith.order = newOrder;
    const tSave = convertBlockForAPI(target);
    const sSave = convertBlockForAPI(swapWith);
    fetch(`/api/theory/blocks/${target.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: tSave.type, content: tSave.content, parent_id: tSave.parent_id ?? null, order: tSave.order }),
    })
      .then(() =>
        fetch(`/api/theory/blocks/${swapWith.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: sSave.type, content: sSave.content, parent_id: sSave.parent_id ?? null, order: sSave.order }),
        })
      )
      .then(() => fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) => r.json()))
      .then((data) => {
        if (data.blocks) data.blocks = convertBlocksFromAPI(data.blocks);
        setTheory(data);
      })
      .catch(console.error);
  }

  return (
    <div className="form-root">
      <div className="form-header">
        <h1>Редактор теории</h1>
        <div className="form-tabs">
          <button
            className={activeTab === "theory" ? "form-tab form-tab--active" : "form-tab"}
            onClick={() => setActiveTab("theory")}
          >
            Теория
          </button>
          <button
            className={activeTab === "tasks" ? "form-tab form-tab--active" : "form-tab"}
            onClick={() => setActiveTab("tasks")}
          >
            Теория для заданий
          </button>
          <button
            className={activeTab === "trainers" ? "form-tab form-tab--active" : "form-tab"}
            onClick={() => setActiveTab("trainers")}
          >
            Задания (тренажёры)
          </button>
        </div>
      </div>

      {/* Верхняя панель только для вкладки "theory" */}
      {activeTab === "theory" && (
        <div className="form-top">
          <div className="form-top__group">
            <label>Типы</label>
            <TheoryTypeSelect
              availableTypes={availableTheoryTypes}
              selectedTypeIds={selectedTheoryTypeIds}
              onChange={handleUpdateTheoryTypes}
              disabled={!selectedTheoryId && !isCreatingTheory}
            />
          </div>

          <div className="form-top__group">
            <label>Теория</label>
            <TheorySelect
              theories={theories}
              selectedTheoryId={selectedTheoryId}
              onChange={(id) => {
                setIsCreatingTheory(false);
                setSelectedTheoryId(id);
              }}
              onCreateNew={handleStartCreateTheory}
              disabled={false}
            />
          </div>

          {isCreatingTheory && (
            <div className="form-top__group">
              <label>Новая теория</label>
              <input
                type="text"
                value={newTheoryName}
                onChange={(e) => setNewTheoryName(e.target.value)}
              />
              <button onClick={handleSaveNewTheory} className="form-button--save-theory">
                Сохранить теорию
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === "theory" && (
        <div className="form-main">
          <div className="form-tree">
            <div className="form-tree__header">Блоки теории</div>
            <div className="form-tree__scroll">
              <BlocksTree
                theory={theory}
                selectedBlockId={selectedBlockId}
                onSelectBlock={(id) => setSelectedBlockId(id)}
                onAddBlockInGroup={(groupId) => {
                  if (!selectedTheoryId) return;
                  createBlockAt(selectedTheoryId, groupId)
                    .then((updated) => setTheory(updated))
                    .catch(console.error);
                }}
                onMoveBlock={handleMoveBlock}
              />
            </div>
            <button
              className="form-tree__add"
              onClick={() => {
                if (!selectedTheoryId) return;
                createBlockAt(selectedTheoryId, null).then(setTheory).catch(console.error);
              }}
              disabled={!selectedTheoryId}
            >
              + Добавить блок в корень
            </button>
          </div>

          <div className="form-editor">
            <div className="form-editor__header">Редактор блока</div>
            <BlockEditor block={blockDraft} onChange={setBlockDraft} disabled={!selectedBlockId} />
            <div className="form-editor__actions">
              <button onClick={handleSaveBlock} disabled={!canSaveBlock}>
                Сохранить блок
              </button>
              <button onClick={handleDeleteBlock} disabled={!canSaveBlock} className="form-editor__delete">
                Удалить блок
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "tasks" && <TasksTheoryEditor theories={theories} />}

      {activeTab === "trainers" && <TasksAdmin />}
    </div>
  );
}

export default FormApp;
