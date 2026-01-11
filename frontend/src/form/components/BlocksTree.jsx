import React from "react";

// строим дерево из плоского списка
function buildTree(blocks) {
  const byId = new Map();
  blocks.forEach((b) => byId.set(b.id, { ...b, children: [] }));

  const roots = [];
  byId.forEach((node) => {
    if (node.parent_id == null) {
      roots.push(node);
    } else {
      const parent = byId.get(node.parent_id);
      if (parent) parent.children.push(node);
      else roots.push(node);
    }
  });

  const sortRec = (nodes) => {
    nodes.sort((a, b) => a.order - b.order);
    nodes.forEach((n) => sortRec(n.children));
  };
  sortRec(roots);
  return roots;
}

function TreeNode({ node, level, selectedBlockId, onSelectBlock }) {
  const paddingLeft = 8 + level * 20; // больше отступ для вложенности

  return (
    <>
      <div
        className={
          "form-tree__item" +
          (node.id === selectedBlockId ? " form-tree__item--active" : "")
        }
        style={{ paddingLeft }}
        onClick={() => onSelectBlock(node.id)}
      >
        <span className="form-tree__order">#{node.order}</span>
        <span className="form-tree__type">{node.type}</span>
        <span className="form-tree__content">
          {node.content.slice(0, 60) || "(пусто)"}
        </span>
      </div>
      {node.children.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          level={level + 1}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
        />
      ))}
    </>
  );
}

export function BlocksTree({ theory, selectedBlockId, onSelectBlock, onAddBlock }) {
  const tree = theory ? buildTree(theory.blocks) : [];

  return (
    <div className="form-tree">
      <div className="form-tree__header">Блоки</div>
      <div className="form-tree__scroll">
        {tree.map((node) => (
          <TreeNode
            key={node.id}
            node={node}
            level={0}
            selectedBlockId={selectedBlockId}
            onSelectBlock={onSelectBlock}
          />
        ))}
      </div>
      <button
        className="form-tree__add"
        onClick={onAddBlock}
        disabled={!theory}
      >
        Добавить блок
      </button>
    </div>
  );
}
