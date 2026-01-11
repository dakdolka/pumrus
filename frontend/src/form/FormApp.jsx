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

  // плоский список ТОЛЬКО для поиска блока по id
  function flattenBlocks(nodes) {
    if (!Array.isArray(nodes)) return [];
    const res = [];
    const walk = (arr) => {
      arr.forEach((n) => {
        res.push(n);
        if (Array.isArray(n.children) && n.children.length) {
          walk(n.children);
        }
      });
    };
    walk(nodes);
    return res;
  }

  // собрать детей конкретного родителя по дереву:
  // - parentId == null -> корневые блоки (theory.blocks)
  // - иначе -> children найденной группы
  function collectChildrenForParent(blocks, parentId) {
    if (parentId == null) {
      return blocks || [];
    }

    const res = [];

    const walk = (nodes) => {
      if (!Array.isArray(nodes)) return;
      nodes.forEach((n) => {
        if (n.id === parentId) {
          if (Array.isArray(n.children)) {
            res.push(...n.children);
          }
        } else if (Array.isArray(n.children) && n.children.length) {
          walk(n.children);
        }
      });
    };

    walk(blocks || []);
    return res;
  }

  // создать блок в корне или группе и вернуть обновлённую теорию
  async function createBlockAt(theoryId, parentId) {
    const currentTheory = theory;
    const blocks = currentTheory?.blocks || [];

    const siblings = collectChildrenForParent(blocks, parentId);
    let order = 0;
    if (siblings.length > 0) {
      const sorted = [...siblings].sort(
        (a, b) => (a.order ?? 0) - (b.order ?? 0)
      );
      const last = sorted[sorted.length - 1];
      order = (last.order ?? 0) + 1;
    }

    await fetch(`/api/theory/${theoryId}/blocks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        type: "text",
        content: "",
        parent_id: parentId, // null для корня, id группы для вложения
        order,               // обязателен по схеме
      }),
    });

    const updatedTheory = await fetch(
      `/api/theory/get_theory/${theoryId}`
    ).then((r) => r.json());

    // выбираем только что добавленный блок как активный
    const flat = flattenBlocks(updatedTheory.blocks || []);
    if (flat.length > 0) {
      const maxIdBlock = flat.reduce((acc, b) =>
        !acc || b.id > acc.id ? b : acc
      , null);
      if (maxIdBlock) {
        setSelectedBlockId(maxIdBlock.id);
      }
    }

    return updatedTheory;
  }

  // 1. загрузка предметов + типов
  useEffect(() => {
    fetch("/api/theory/all_theory_dop_info")
      .then((r) => r.json())
      .then(setSubjects)
      .catch(console.error);
  }, []);

  // 2. выбор предмета -> загрузка теорий по предмету
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

    const allBlocks = flattenBlocks(theory.blocks || []);
    const block = allBlocks.find((b) => b.id === selectedBlockId);
    if (!block) return;

    setBlockDraft({
      type: block.type,
      content: block.content,
      parent_id: null,          // вложенность не трогаем
      order: block.order ?? 0,
    });
  }, [selectedBlockId, theory]);

  // --- handlers теории ---
  function handleStartCreateTheory() {
    resetTheoryState();
    setSelectedTheoryTypeIds([]);
    setIsCreatingTheory(true);
    setNewTheoryName("");
  }

  function handleSaveNewTheory() {
    if (!newTheoryName.trim() || !selectedSubjectId) return;

    const subjectObj = subjects.find((s) => s.id === selectedSubjectId);

    fetch("/api/theory/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
      },
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

  // --- блоки: только обновление/удаление через форму ---
  function handleSaveBlock() {
    if (!selectedBlockId) return;

    fetch(`/api/theory/blocks/${selectedBlockId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
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

  const canSaveBlock = !!selectedBlockId;

  return (
    <div className="form-root">
      <div className="form-header">
        <h1>Редактор теории</h1>
      </div>

      <div className="form-top">
        <div className="form-top__group">
          <label>Предмет:</label>
          <SubjectSelect
            subjects={subjects}
            selectedSubjectId={selectedSubjectId}
            onChange={setSelectedSubjectId}
          />
        </div>

        <div className="form-top__group">
          <label>Теория:</label>
          <TheorySelect
            theories={theories}
            selectedTheoryId={selectedTheoryId}
            onChange={(id) => {
              setSelectedTheoryId(id);
              setIsCreatingTheory(false);
              setNewTheoryName("");
            }}
            onCreateNew={handleStartCreateTheory}
            disabled={!selectedSubjectId}
          />
        </div>

        {isCreatingTheory && (
          <div className="form-top__group">
            <label>Новая:</label>
            <input
              type="text"
              className="form-input"
              value={newTheoryName}
              onChange={(e) => setNewTheoryName(e.target.value)}
              placeholder="Название теории"
            />
            <button
              className="form-button form-button--save-theory"
              onClick={handleSaveNewTheory}
            >
              Сохранить теорию
            </button>
          </div>
        )}

        {selectedSubjectId && (
          <TheoryTypeSelect
            availableTypes={availableTheoryTypes}
            selectedTypeIds={selectedTheoryTypeIds}
            onChange={handleUpdateTheoryTypes}
            disabled={!selectedTheoryId && !isCreatingTheory}
          />
        )}
      </div>

      <div className="form-main">
        <div className="form-tree">
          <h2 className="form-tree__header">Структура блоков</h2>
          <BlocksTree
            blocks={theory?.blocks || []}
            selectedBlockId={selectedBlockId}
            onSelectBlock={setSelectedBlockId}
            onAddRootBlock={async () => {
              if (!selectedTheoryId) return;
              const updated = await createBlockAt(selectedTheoryId, null);
              setTheory(updated);
            }}
            onAddBlockInGroup={async (groupId) => {
              if (!selectedTheoryId) return;
              const updated = await createBlockAt(selectedTheoryId, groupId);
              setTheory(updated);
            }}
          />
        </div>

        <div className="form-editor">
          <h2 className="form-editor__header">Редактор блока</h2>
          {theory ? (
            <BlockEditor
              selectedBlockId={selectedBlockId}
              blockDraft={blockDraft}
              setBlockDraft={setBlockDraft}
              canSave={canSaveBlock}
              onSaveBlock={handleSaveBlock}
              onDeleteBlock={handleDeleteBlock}
            />
          ) : (
            <div style={{ opacity: 0.7, fontSize: "0.9rem" }}>
              Выберите или создайте теорию, чтобы работать с блоками
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default FormApp;
