export function buildTheoryTree(blocks = []) {
  if (blocks.some((block) => Array.isArray(block.children))) return blocks;

  const children = new Map();
  const ids = new Set(blocks.map((block) => block.id));
  blocks.forEach((block) => {
    const parent = block.parentId != null && ids.has(block.parentId)
      ? block.parentId
      : null;
    children.set(parent, [...(children.get(parent) || []), block]);
  });
  children.forEach((items) => items.sort(
    (left, right) => (left.sortOrder ?? 0) - (right.sortOrder ?? 0)
      || String(left.id).localeCompare(String(right.id)),
  ));

  const attach = (block, ancestors = new Set()) => {
    if (ancestors.has(block.id)) return { ...block, children: [] };
    const next = new Set(ancestors).add(block.id);
    return {
      ...block,
      children: (children.get(block.id) || []).map((item) => attach(item, next)),
    };
  };

  return (children.get(null) || []).map((block) => attach(block));
}
