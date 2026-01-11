import React, { useEffect, useState } from "react";
import "./form.css";

import { SubjectSelect } from "./components/SubjectSelect";
import { TheorySelect } from "./components/TheorySelect";
import { BlocksTree } from "./components/BlocksTree";
import { BlockEditor } from "./components/BlockEditor";
import { TheoryTypeSelect } from "./components/TheoryTypeSelect";

function FormApp() {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);

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

  const currentSubject = subjects.find((s) => s.id === selectedSubjectId);
  const availableTheoryTypes = currentSubject?.types || [];

  function resetTheoryState() {
    setSelectedTheoryId(null);
    setTheory(null);
    setSelectedBlockId(null);
    setBlockDraft({
      type: "text",
      content: "",
      parent_id: null,
      order: 0,
    });
  }

  // --- утилита: плоский список блоков с parent_id на основе children ---
  function getFlatBlocksFromTheory(theoryData) {
    if (!theoryData || !Array.isArray(theoryData.blocks)) return [];
    const flatten = (nodes, parentId = null) => {
      const res = [];
      nodes.forEach((n) => {
        res.push({ ...n, parent_id: n.parent_id ?? parentId });
        if (Array.isArray(n.children) && n.children.length) {
          res.push(...flatten(n.children, n.id));
        }
      });
      return res;
    };
    return flatten(theoryData.blocks);
  }

  // --- API-хелпер: создать блок в корне или группе и вернуть обновлённую теорию ---
  async function createBlockAt(theoryId, parentId) {
    // 1. свежая теория
    const theoryData = await fetch(
      `/api/theory/get_theory/${theoryId}`
    ).then((r) => r.json());
    const all = getFlatBlocksFromTheory(theoryData);

    // 2. считаем order среди соседей
    const siblings = all.filter((b) =>
      parentId == null ? b.parent_id == null : b.parent_id === parentId
    );
    let order = 0;
    if (siblings.length > 0) {
      const sorted = [...siblings].sort(
        (a, b) => (a.order ?? 0) - (b.order ?? 0)
      );
      const last = sorted[sorted.length - 1];
      order = (last.order ?? 0) + 1;
    }

    // 3. POST блока
    await fetch(`/api/theory/${theoryId}/blocks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "text",
        content: "",
        parent_id: parentId,
        order,
      }),
    });

    // 4. обновлённая теория
    const updatedTheory = await fetch(
      `/api/theory/get_theory/${theoryId}`
    ).then((r) => r.json());

    return updatedTheory;
  }

  // 1. загрузка предметов + типов
  useEffect(() => {
    fetch("/api/theory/all_theory_dop_info")
      .then((r) => r.json())
      .then(setSubjects)
      .catch(console.error);
  }, []);

  // 2. выбор предмета -> загрузка теорий по предмету (с типами)
  useEffect(() => {
    if (!selectedSubjectId) return;
    fetch(`/api/theory/all_theory_for_subject/${selectedSubjectId}`)
      .then((r) => r.json())
      .then((data) => {
        setTheories(data);

        if (selectedTheoryId) {
          const t = data.find((th) => th.id === selectedTheoryId);
          if (t && Array.isArray(t.types)) {
            setSelectedTheoryTypeIds(t.types.map((tt) => tt.id));
          } else {
            setSelectedTheoryTypeIds([]);
          }
        } else {
          setSelectedTheoryTypeIds([]);
        }
      })
      .catch(console.error);
  }, [selectedSubjectId]);

  // 3. выбор теории -> загрузка теории с блоками
  useEffect(() => {
    if (!selectedTheoryId) return;

    const t = theories.find((th) => th.id === selectedTheoryId);
    if (t && Array.isArray(t.types)) {
      setSelectedTheoryTypeIds(t.types.map((tt) => tt.id));
    } else {
      setSelectedTheoryTypeIds([]);
    }

    fetch(`/api/theory/get_theory/${selectedTheoryId}`)
      .then((r) => r.json())
      .then((data) => {
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({
          type: "text",
          content: "",
          parent_id: null,
          order: 0,
        });
      })
      .catch(console.error);
  }, [selectedTheoryId, theories]);

  // 4. когда выбрали блок — заполняем форму его данными
  useEffect(() => {
    if (!theory || !selectedBlockId) return;

    const allBlocks = getFlatBlocksFromTheory(theory);
    const block = allBlocks.find((b) => b.id === selectedBlockId);
    if (!block) return;

    setBlockDraft({
      type: block.type,
      content: block.content,
      parent_id: block.parent_id ?? null,
      order: block.order,
    });
  }, [selectedBlockId, theory]);

  // --- handlers теории ---

  function handleStartCreateTheory() {
    resetTheoryState();
    setSelectedTheoryTypeIds([]);
    setIsCreatingTheory(false);
    setNewTheoryName("");

    const name = window.prompt("Название новой теории:");
    if (!name) {
      return;
    }
    setNewTheoryName(name);
    setIsCreatingTheory(true);
  }

  function handleSaveNewTheory() {
    if (!newTheoryName.trim() || !selectedSubjectId) return;

    const subjectObj = subjects.find((s) => s.id === selectedSubjectId);

    fetch("/api/theory/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newTheoryName.trim(),
        subject: subjectObj?.subject,
        type_ids: selectedTheoryTypeIds,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        const typesForNewTheory = availableTheoryTypes.filter((t) =>
          selectedTheoryTypeIds.includes(t.id)
        );

        const enriched = {
          id: data.id,
          name: data.name,
          types: typesForNewTheory,
        };

        setTheories((prev) => [...prev, enriched]);
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
      body: JSON.stringify({
        type_ids: newTypeIds,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        setTheory(data);

        const newTypes = availableTheoryTypes.filter((t) =>
          newTypeIds.includes(t.id)
        );

        setTheories((prev) =>
          prev.map((th) =>
            th.id === selectedTheoryId ? { ...th, types: newTypes } : th
          )
        );
      })
      .catch(console.error);
  }

  // --- handlers блоков (через форму) ---

  function handleCreateBlock() {
    if (!selectedTheoryId) return;
    fetch(`/api/theory/${selectedTheoryId}/blocks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(blockDraft),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) =>
          r.json()
        )
      )
      .then(setTheory)
      .catch(console.error);
  }

  function handleSaveBlock() {
    if (!selectedBlockId) return;
    fetch(`/api/theory/blocks/${selectedBlockId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(blockDraft),
    })
      .then((r) => r.json())
      .then(() =>
        fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) =>
          r.json()
        )
      )
      .then(setTheory)
      .catch(console.error);
  }

  function handleDeleteBlock() {
    if (!selectedBlockId) return;
    if (!window.confirm("Удалить блок?")) return;

    fetch(`/api/theory/blocks/${selectedBlockId}`, {
      method: "DELETE",
    })
      .then(() =>
        fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) =>
          r.json()
        )
      )
      .then((data) => {
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({
          type: "text",
          content: "",
          parent_id: null,
          order: 0,
        });
      })
      .catch(console.error);
  }

  return (
    <div className="form-root">
      <div className="form-header">
        <h1>Редактор теории</h1>
      </div>

      <div className="form-top">
        <SubjectSelect
          subjects={subjects}
          selectedSubjectId={selectedSubjectId}
          onChange={(id) => {
            setSelectedSubjectId(id);
            resetTheoryState();
            setSelectedTheoryTypeIds([]);
            setIsCreatingTheory(false);
            setNewTheoryName("");
          }}
        />

        <TheoryTypeSelect
          availableTypes={availableTheoryTypes}
          selectedTypeIds={selectedTheoryTypeIds}
          onChange={handleUpdateTheoryTypes}
          disabled={!selectedSubjectId}
        />

        <div className="form-top__group">
          <label>Теория:</label>
          {isCreatingTheory ? (
            <>
              <input
                type="text"
                value={newTheoryName}
                onChange={(e) => setNewTheoryName(e.target.value)}
                placeholder="Название новой теории"
              />
              <button
                style={{ backgroundColor: "#2e7d32" }}
                onClick={handleSaveNewTheory}
                disabled={!newTheoryName.trim() || !selectedSubjectId}
              >
                Сохранить теорию
              </button>
            </>
          ) : (
            <>
              <TheorySelect
                theories={theories}
                selectedTheoryId={selectedTheoryId}
                onChange={setSelectedTheoryId}
                disabled={!selectedSubjectId}
              />
              <button
                onClick={handleStartCreateTheory}
                disabled={!selectedSubjectId}
              >
                Создать новую теорию
              </button>
            </>
          )}
        </div>
      </div>

      <div className="form-main">
        <div className="form-tree">
          <div className="form-tree__header">Блоки теории</div>

          {theory ? (
            <BlocksTree
                blocks={theory.blocks || []}
                selectedBlockId={selectedBlockId}
                onSelectBlock={setSelectedBlockId}
                onAddRootBlock={async () => {
                if (!selectedTheoryId) return;
                const updatedTheory = await createBlockAt(selectedTheoryId, null);

                // найдём только что созданный корневой блок
                const all = getFlatBlocksFromTheory(updatedTheory);
                const roots = all.filter((b) => b.parent_id == null);
                let newBlock = null;
                if (roots.length > 0) {
                    const sorted = [...roots].sort(
                    (a, b) => (a.order ?? 0) - (b.order ?? 0)
                    );
                    newBlock = sorted[sorted.length - 1];
                }

                setTheory(updatedTheory);
                setSelectedBlockId(newBlock ? newBlock.id : null);
                setBlockDraft({
                    type: "text",
                    content: "",
                    parent_id: null,
                    order: 0,
                });
                }}
                onAddBlockInGroup={async (groupId) => {
                if (!selectedTheoryId) return;
                const updatedTheory = await createBlockAt(selectedTheoryId, groupId);

                // найдём только что созданного ребёнка этой группы
                const all = getFlatBlocksFromTheory(updatedTheory);
                const children = all.filter((b) => b.parent_id === groupId);
                let newBlock = null;
                if (children.length > 0) {
                    const sorted = [...children].sort(
                    (a, b) => (a.order ?? 0) - (b.order ?? 0)
                    );
                    newBlock = sorted[sorted.length - 1];
                }

                setTheory(updatedTheory);
                setSelectedBlockId(newBlock ? newBlock.id : null);
                setBlockDraft({
                    type: "text",
                    content: "",
                    parent_id: null,
                    order: 0,
                });
                }}
            />
            ) : (
            <div className="form-tree__scroll">
                <div style={{ opacity: 0.7, fontSize: "0.9rem" }}>
                Выберите или создайте теорию
                </div>
            </div>
            )}
        </div>

        <div className="form-editor">
          <div className="form-editor__header">Редактор блока</div>
          <BlockEditor
            selectedBlockId={selectedBlockId}
            blockDraft={blockDraft}
            setBlockDraft={setBlockDraft}
            canSave={!!selectedBlockId}
            onSaveBlock={handleSaveBlock}
            onDeleteBlock={handleDeleteBlock}
        />
        </div>
      </div>
    </div>
  );
}

export default FormApp;
