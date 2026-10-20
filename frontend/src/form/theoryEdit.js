import { theoryAnchorId, theoryHref } from "../theory/theoryLinks.js";
export const THEORY_EDIT_FORMAT = "pumrus.theory-edit";
const TYPES = new Set(["rich_text", "section", "callout", "example", "list", "table", "image", "video_embed", "practice_link", "theory_link"]);
const clone = (value) => JSON.parse(JSON.stringify(value));
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

export function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (object(value)) return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}

function keys(value, allowed, path) {
  if (!object(value)) throw new Error(`${path}: ожидается объект { … }`);
  const extra = Object.keys(value).find((key) => !allowed.includes(key));
  if (extra) throw new Error(`${path}.${extra}: неизвестное поле. Проверьте название.`);
}

function text(value, path, max) {
  if (typeof value !== "string" || !value.trim() || value.length > max) throw new Error(`${path}: укажите текст от 1 до ${max} символов`);
}

function validateData(block, path) {
  if (block.type === "theory_link" && !theoryHref(block.data)) throw new Error(`${path}.data: укажите положительные целые taskNumber и topicId и корректную метку anchor`);
  for (const key of ["markdown", "title", "url", "alt", "caption", "svg", "buttonLabel"]) {
    if (key in block.data && typeof block.data[key] !== "string") throw new Error(`${path}.data.${key}: ожидается текст`);
  }
  if (block.type === "callout" && !["note", "rule", "warning", "important", "tip"].includes(block.data.variant ?? "note")) throw new Error(`${path}.data.variant: неизвестный вид выноски`);
  const validCell = (cell) => ["string", "number"].includes(typeof cell) || (object(cell) && typeof cell.text === "string");
  if (block.type === "table" && (("rows" in block.data && !Array.isArray(block.data.rows)) || (block.data.rows || []).some((row) => { const cells = object(row) ? row.cells : row; return !Array.isArray(cells) || !cells.every(validCell); }))) throw new Error(`${path}.data.rows: строки должны содержать cells: ["текст", …]`);
  if (block.type === "list" && (("items" in block.data && !Array.isArray(block.data.items)) || (block.data.items || []).some((item) => typeof item !== "string" && !(object(item) && typeof item.text === "string")))) throw new Error(`${path}.data.items: ожидается список строк`);
  if (block.type === "list" && !["ordered", "unordered"].includes(block.data.style ?? "unordered")) throw new Error(`${path}.data.style: ordered или unordered`);
}

export function flattenEditPage(page, path = "after") {
  keys(page, ["title", "ownerTitle", "description", "blocks"], path);
  text(page.title, `${path}.title`, 256);
  text(page.ownerTitle, `${path}.ownerTitle`, 256);
  if (page.description !== undefined && (typeof page.description !== "string" || page.description.length > 1024)) throw new Error(`${path}.description: текст до 1024 символов`);
  if (!Array.isArray(page.blocks)) throw new Error(`${path}.blocks: ожидается список блоков [ … ]`);
  const flat = [], ids = new Set(), anchors = new Set();
  function walk(blocks, parentId, ancestors) {
    if (ancestors.length > 32) throw new Error("Вложенность блоков не должна превышать 32 уровня");
    blocks.forEach((block, sortOrder) => {
      const indices = [...ancestors, sortOrder];
      const label = `${path}.blocks[${indices.join("].children[")}]`;
      keys(block, ["id", "type", "data", "settings", "children"], label);
      if (!TYPES.has(block.type)) throw new Error(`${label}.type: неизвестный тип блока`);
      if (flat.length >= 2000) throw new Error("В теме допускается не более 2000 блоков");
      if (block.id != null) text(block.id, `${label}.id`, 96);
      const id = block.id || `new:auto:${flat.length + 1}`;
      if (ids.has(id)) throw new Error(`${label}.id: повторяется идентификатор «${id}»`);
      ids.add(id);
      if (block.data !== undefined && !object(block.data)) throw new Error(`${label}.data: ожидается объект`);
      if (block.settings !== undefined && !object(block.settings)) throw new Error(`${label}.settings: ожидается объект`);
      const normalized = {id, type:block.type, data:block.data || {}, settings:block.settings || {}, parentId, sortOrder};
      const anchor = normalized.settings.anchor;
      if (anchor != null && anchor !== "") {
        if (!theoryAnchorId(anchor)) throw new Error(`${label}.settings.anchor: используйте латинские строчные буквы, цифры и дефис; начните с буквы (до 64 символов)`);
        if (anchors.has(anchor)) throw new Error(`${label}.settings.anchor: повторяется метка раздела`);
        anchors.add(anchor);
      }
      validateData(normalized, label);
      flat.push({...normalized, path:indices});
      if (block.children !== undefined && !Array.isArray(block.children)) throw new Error(`${label}.children: ожидается список`);
      walk(block.children || [], id, indices);
    });
  }
  walk(page.blocks, null, []);
  return flat;
}

function canonicalPage(page) {
  const flat = flattenEditPage(page);
  return {title:page.title, ownerTitle:page.ownerTitle, description:page.description || "", blocks:flat.map(({path: _path, ...block}) => block)};
}

export function parseTheoryEdit(source, expected) {
  if (source.length > 2_000_000) throw new Error("Пакет слишком большой: максимум 2 МБ");
  let value;
  try { value = JSON.parse(source.trim().replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/i, "$1")); }
  catch (error) { throw new Error(`Ошибка JSON: ${error.message}`); }
  keys(value, ["format", "schemaVersion", "base", "before", "after"], "Пакет");
  if (value.format !== THEORY_EDIT_FORMAT || value.schemaVersion !== 1) throw new Error('Ожидается format: "pumrus.theory-edit", schemaVersion: 1');
  keys(value.base, ["documentId", "publishedVersionId", "fingerprint"], "base");
  if (!Number.isSafeInteger(value.base.documentId) || value.base.documentId < 1 || !(value.base.publishedVersionId === null || (Number.isSafeInteger(value.base.publishedVersionId) && value.base.publishedVersionId > 0)) || !/^[0-9a-f]{64}$/.test(value.base.fingerprint)) throw new Error("Некорректный base. Используйте экспорт темы из формы");
  if (expected && stableJson(value.base) !== stableJson(expected.base)) throw new Error("Пакет относится к другой теме или старой версии. Экспортируйте тему заново");
  const before = canonicalPage(value.before);
  const after = canonicalPage(value.after);
  if (expected && stableJson(before) !== stableJson(canonicalPage(expected.before))) throw new Error("Раздел before изменён. Вносите правки только в after");
  return {package:value, before, after, blocks:flattenEditPage(value.after), changed:stableJson(before) !== stableJson(after)};
}

export function editPackageBlock(value, id, patch, remove = false) {
  const next = clone(value);
  // Inspector fields may temporarily be incomplete; keep them editable until
  // validation succeeds again. Publication still requires parseTheoryEdit.
  let count = 0;
  function update(blocks) {
    for (let index = 0; index < blocks.length; index++) {
      count++;
      const block = blocks[index], blockId = block.id || `new:auto:${count}`;
      if (blockId === id) {
        if (remove) blocks.splice(index, 1);
        else blocks[index] = {...block, id, ...patch};
        return true;
      }
      if (update(block.children || [])) return true;
    }
    return false;
  }
  if (!update(next.after.blocks)) throw new Error("Блок не найден в after");
  return next;
}

export function prettyPackage(value) { return JSON.stringify(value, null, 2); }
