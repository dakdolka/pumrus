import React, { useEffect, useState } from "react";
import "./form.css";
import { SubjectSelect } from "./components/SubjectSelect";
import { TheorySelect } from "./components/TheorySelect";
import { BlocksTree } from "./components/BlocksTree";
import { BlockEditor } from "./components/BlockEditor";

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

  // 1. загрузка предметов
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
      .then(setTheories)
      .catch(console.error);
  }, [selectedSubjectId]);

  // 3. выбор теории -> загрузка теории с блоками
  useEffect(() => {
    if (!selectedTheoryId) return;
    fetch(`/api/theory/get_theory/${selectedTheoryId}`)
      .then((r) => r.json())
      .then((data) => {
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({ type: "text", content: "", parent_id: null, order: 0 });
      })
      .catch(console.error);
  }, [selectedTheoryId]);

  // 4. когда выбрали блок — заполняем форму его данными
  useEffect(() => {
    if (!theory || !selectedBlockId) return;
    const block = theory.blocks.find((b) => b.id === selectedBlockId);
    if (!block) return;
    setBlockDraft({
      type: block.type,
      content: block.content,
      parent_id: block.parent_id,
      order: block.order,
    });
  }, [selectedBlockId, theory]);

  // --- handlers ---

  function handleCreateTheory() {
    const name = prompt("Название новой теории:");
    if (!name || !selectedSubjectId) return;

    const subjectObj = subjects.find((s) => s.id === selectedSubjectId);

    fetch("/api/theory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        subject: subjectObj?.subject,
        type_ids: [],
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        setTheories((prev) => [...prev, data]);
        setSelectedTheoryId(data.id);
      })
      .catch(console.error);
  }

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
    fetch(`/api/theory/blocks/${selectedBlockId}`, { method: "DELETE" })
      .then(() =>
        fetch(`/api/theory/get_theory/${selectedTheoryId}`).then((r) =>
          r.json()
        )
      )
      .then((data) => {
        setTheory(data);
        setSelectedBlockId(null);
        setBlockDraft({ type: "text", content: "", parent_id: null, order: 0 });
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
            setSelectedTheoryId(null);
            setTheory(null);
          }}
        />
        <TheorySelect
          theories={theories}
          selectedTheoryId={selectedTheoryId}
          onChange={setSelectedTheoryId}
          onCreate={handleCreateTheory}
          disabled={!selectedSubjectId}
        />
      </div>

      <div className="form-main">
        <BlocksTree
          theory={theory}
          selectedBlockId={selectedBlockId}
          onSelectBlock={setSelectedBlockId}
          onAddBlock={() => {
            const count = theory ? theory.blocks.length : 0;
            setSelectedBlockId(null);
            setBlockDraft({
              type: "text",
              content: "",
              parent_id: null,
              order: count,
            });
          }}
        />
        <BlockEditor
          selectedBlockId={selectedBlockId}
          blockDraft={blockDraft}
          setBlockDraft={setBlockDraft}
          canCreate={!!theory}
          canSave={!!selectedBlockId}
          onCreateBlock={handleCreateBlock}
          onSaveBlock={handleSaveBlock}
          onDeleteBlock={handleDeleteBlock}
        />
      </div>
    </div>
  );
}

export default FormApp;
