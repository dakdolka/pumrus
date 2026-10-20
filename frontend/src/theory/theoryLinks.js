const ANCHOR = /^[a-z][a-z0-9-]{0,63}$/;

export function theoryAnchorId(anchor) {
  return typeof anchor === "string" && ANCHOR.test(anchor) ? `theory-${anchor}` : "";
}

export function theoryHref(data) {
  if (!Number.isSafeInteger(data?.taskNumber) || data.taskNumber <= 0 || !Number.isSafeInteger(data?.topicId) || data.topicId <= 0) return "";
  if (data.anchor != null && typeof data.anchor !== "string") return "";
  if (data.anchor && !theoryAnchorId(data.anchor)) return "";
  return `/theory/tasks/${data.taskNumber}/topics/${data.topicId}${data.anchor ? `#${theoryAnchorId(data.anchor)}` : ""}`;
}

export function revealTheoryAnchor(root, hash) {
  const id = hash.replace(/^#/, "");
  if (!/^theory-[a-z][a-z0-9-]{0,63}$/.test(id)) return false;
  const target = root?.querySelector(`[id="${id}"]`);
  if (!target) return false;
  for (let node = target; node && node !== root; node = node.parentElement) {
    if (node.tagName === "DETAILS") node.open = true;
  }
  target.scrollIntoView({ block: "start", behavior: "auto" });
  target.focus({ preventScroll: true });
  return true;
}
