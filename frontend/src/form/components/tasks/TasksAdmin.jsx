import React, { useState, useEffect, useCallback, useRef } from "react";
import GroupsTab    from "./GroupsTab";
import OptionsTab   from "./OptionsTab";
import OptionSetsTab from "./OptionSetsTab";
import TasksTab     from "./TasksTab";

const TABS = [
  { key: "groups",      label: "Группы" },
  { key: "options",     label: "Опции" },
  { key: "option-sets", label: "Наборы опций" },
  { key: "tasks",       label: "Задания" },
];

export function TasksAdmin() {
  const [activeTab,  setActiveTab]  = useState("groups");
  const [groups,     setGroups]     = useState([]);
  const [options,    setOptions]    = useState([]);
  const [optionSets, setOptionSets] = useState([]);

  // каждый дочерний таб регистрирует свою autoSave сюда
  const tabSaveRef = useRef(null);

  const loadGroups = useCallback(() =>
    fetch("/api/tasks/general/groups")
      .then(r => r.json()).then(setGroups).catch(console.error), []);

  const loadOptions = useCallback(() =>
    fetch("/api/tasks/general/options")
      .then(r => r.json()).then(setOptions).catch(console.error), []);

  const loadOptionSets = useCallback(() =>
    fetch("/api/tasks/general/option-sets")
      .then(r => r.json()).then(setOptionSets).catch(console.error), []);

  useEffect(() => {
    loadGroups();
    loadOptions();
    loadOptionSets();
  }, []);

  const handleTabSwitch = async (key) => {
    if (key === activeTab) return;
    if (tabSaveRef.current) await tabSaveRef.current();
    setActiveTab(key);
  };

  const registerAutoSave = useCallback((fn) => {
    tabSaveRef.current = fn;
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div className="form-tabs" style={{ marginBottom: 10 }}>
        {TABS.map(t => (
          <button
            key={t.key}
            className={activeTab === t.key ? "form-tab form-tab--active" : "form-tab"}
            onClick={() => handleTabSwitch(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "groups" && (
        <GroupsTab
          groups={groups}
          onReload={loadGroups}
          registerAutoSave={registerAutoSave}
        />
      )}
      {activeTab === "options" && (
        <OptionsTab
          options={options}
          onReload={loadOptions}
          registerAutoSave={registerAutoSave}
        />
      )}
      {activeTab === "option-sets" && (
        <OptionSetsTab
          optionSets={optionSets}
          options={options}
          onReload={loadOptionSets}
          registerAutoSave={registerAutoSave}
        />
      )}
      {activeTab === "tasks" && (
        <TasksTab
          groups={groups}
          options={options}
          optionSets={optionSets}
          registerAutoSave={registerAutoSave}
        />
      )}
    </div>
  );
}
