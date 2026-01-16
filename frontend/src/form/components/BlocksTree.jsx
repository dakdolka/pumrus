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
  walk(blocks || []);
  return ids;
}

function TreeNode({
  node,
  level,
  selectedBlockId,
  onSelectBlock,
  onAddBlockInGroup,
  onMoveBlock,
}) {
  const paddingLeft = 8 + level * 20;

  const preview =
    node.content && typeof node.content === "string"
      ? node.content.replace(/\s+/g, " ").slice(0, 60)
      : "";

  const children = Array.isArray(node.children)
    ? [...node.children].sort(
        (a, b) => (a.order ?? 0) - (b.order ?? 0)
      )
    : [];

  const isActive = selectedBlockId === node.id;
  const hasChildren = children.length > 0; // группа = есть дети

  return (
    <>
      <div
        className={
          isActive
            ? "form-tree__item form-tree__item--active"
            : "form-tree__item"
        }
        style={{ paddingLeft }}
        onClick={() => {
          onSelectBlock(node.id);
        }}
      >
        {onMoveBlock && (
          <div className="form-tree__move-vertical">
            <button
              type="button"
              className="form-tree__move-btn"
              onClick={(e) => {
                e.stopPropagation();
                onMoveBlock(node.id, "up");
              }}
            >
              ↑
            </button>
            <button
              type="button"
              className="form-tree__move-btn"
              onClick={(e) => {
                e.stopPropagation();
                onMoveBlock(node.id, "down");
              }}
            >
              ↓
            </button>
          </div>
        )}

        <span className="form-tree__order">
          {typeof node.order === "number" ? node.order : "-"}
        </span>
        <span className="form-tree__type">{node.type}</span>
        <span className="form-tree__content">{preview}</span>
      </div>

      {children.map((child, index) => {
        const isLastChild = index === children.length - 1;
        return (
          <React.Fragment key={child.id}>
            <TreeNode
              node={child}
              level={level + 1}
              selectedBlockId={selectedBlockId}
              onSelectBlock={onSelectBlock}
              onAddBlockInGroup={onAddBlockInGroup}
              onMoveBlock={onMoveBlock}
            />
            {/* под последним дочерним блоком каждой группы рисуем "+ Блок в группу" */}
            {isLastChild && hasChildren && onAddBlockInGroup && (
              <div
                className="form-tree__add-under-group"
                style={{ paddingLeft: paddingLeft + 20 }}
              >
                <button
                  type="button"
                  className="form-tree__add"
                  onClick={() => onAddBlockInGroup(node.id)}
                >
                  + Блок в группу
                </button>
              </div>
            )}
          </React.Fragment>
        );
      })}
    </>
  );
}

export function BlocksTree({
  theory,
  selectedBlockId,
  onSelectBlock,
  onAddBlockInGroup,
  onMoveBlock,
}) {
  if (!theory || !Array.isArray(theory.blocks)) {
    return (
      <div style={{ opacity: 0.6 }}>
        Нет блоков. Выберите теорию или создайте первый блок.
      </div>
    );
  }

  const blocks = theory.blocks || [];
  const childIds = collectAllChildIds(blocks);
  const rootNodes = blocks.filter((b) => !childIds.has(b.id));

  const sortedRootNodes = [...rootNodes].sort(
    (a, b) => (a.order ?? 0) - (b.order ?? 0)
  );

  if (!sortedRootNodes.length) {
    return (
      <div style={{ opacity: 0.6 }}>
        Нет корневых блоков. Добавьте блок в корень.
      </div>
    );
  }

  return (
    <>
      {sortedRootNodes.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          level={0}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
          onAddBlockInGroup={onAddBlockInGroup}
          onMoveBlock={onMoveBlock}
        />
      ))}
    </>
  );
}
