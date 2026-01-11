import React from "react";

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

  walk(blocks);
  return ids;
}

function TreeNode({
  node,
  level,
  selectedBlockId,
  onSelectBlock,
  onAddBlockInGroup, // (groupId) => void
  onMoveBlock,       // (blockId, direction) => void
}) {
  const paddingLeft = 8 + level * 20;

  const preview =
    node.content && typeof node.content === "string"
      ? node.content.replace(/\s+/g, " ").slice(0, 60)
      : "";

  const children = Array.isArray(node.children)
    ? [...node.children].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    : [];

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
        <div className="form-tree__controls">
          <button
            type="button"
            className="form-tree__move"
            onClick={(e) => {
              e.stopPropagation();      // важно
              onMoveBlock(node.id, "up");
            }}
            title="Переместить выше"
          >
            ↑
          </button>
          <button
            type="button"
            className="form-tree__move"
            onClick={(e) => {
              e.stopPropagation();      // важно
              onMoveBlock(node.id, "down");
            }}
            title="Переместить ниже"
          >
            ↓
          </button>
        </div>

        <span className="form-tree__order">{node.order}</span>
        <span className="form-tree__type">
          {node.type === "group" ? "ГРУППА" : node.type}
        </span>
        <span className="form-tree__content">{preview || "(пусто)"}</span>
      </div>

      {children.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          level={level + 1}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
          onAddBlockInGroup={onAddBlockInGroup}
          onMoveBlock={onMoveBlock}
        />
      ))}

      {node.type === "group" && (
        <div
          style={{
            paddingLeft: paddingLeft + 20,
            marginBottom: 4,
          }}
        >
          <button
            className="form-tree__add"
            onClick={(e) => {
              e.stopPropagation();
              onAddBlockInGroup(node.id);
            }}
          >
            + Блок в группе «{node.content || node.id}»
          </button>
        </div>
      )}
    </>
  );
}

export function BlocksTree({
  blocks,
  selectedBlockId,
  onSelectBlock,
  onAddRootBlock, // () => void
  onAddBlockInGroup, // (groupId) => void
  onMoveBlock,       // (blockId, direction) => void
}) {
  if (!blocks || blocks.length === 0) {
    return (
      <div className="form-tree__scroll">
        <div style={{ opacity: 0.7, fontSize: "0.9rem" }}>
          Блоков пока нет
        </div>
        <button
          className="form-tree__add"
          onClick={onAddRootBlock}
          style={{ marginTop: 8 }}
        >
          + Добавить блок
        </button>
      </div>
    );
  }

  const childIds = collectAllChildIds(blocks);

  const roots = [...blocks]
    .filter((b) => !childIds.has(b.id))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  return (
    <div className="form-tree__scroll">
      {roots.map((root) => (
        <TreeNode
          key={root.id}
          node={root}
          level={0}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
          onAddBlockInGroup={onAddBlockInGroup}
          onMoveBlock={onMoveBlock}
        />
      ))}

      <div style={{ marginTop: 8 }}>
        <button className="form-tree__add" onClick={onAddRootBlock}>
          + Добавить блок
        </button>
      </div>
    </div>
  );
}
