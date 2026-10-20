const MARKERS = { bold: "**", italic: "*", strike: "~~", code: "`" };

export function formatSelection(value, start, end, action, url = "") {
  start = Math.max(0, Math.min(value.length, start));
  end = Math.max(start, Math.min(value.length, end));
  if (["bullet", "number", "quote"].includes(action)) {
    const from = start === 0 ? 0 : value.lastIndexOf("\n", start - 1) + 1;
    const nextLine = value.indexOf("\n", end > start && value[end - 1] === "\n" ? end - 1 : end);
    const to = nextLine === -1 ? value.length : nextLine;
    const lines = value.slice(from, to).split("\n");
    const pattern = action === "bullet" ? /^[-*] / : action === "number" ? /^\d+\. / : /^> /;
    const remove = lines.every((line) => pattern.test(line));
    const changed = lines.map((line, i) => remove ? line.replace(pattern, "") : `${action === "bullet" ? "- " : action === "number" ? `${i + 1}. ` : "> "}${line.replace(pattern, "")}`).join("\n");
    return {value:value.slice(0, from) + changed + value.slice(to), start:from, end:from + changed.length};
  }
  if (action === "newline") return {value:value.slice(0, start) + "\n" + value.slice(end), start:start + 1, end:start + 1};
  let selected = value.slice(start, end);
  if (!selected && action !== "clear") {
    const word = /[\p{L}\p{N}_-]/u;
    while (start > 0 && word.test(value[start - 1])) start--;
    while (end < value.length && word.test(value[end])) end++;
    selected = value.slice(start, end);
  }
  if (action === "clear") {
    const plain = selected.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1").replace(/~~([^~]+)~~/g, "$1").replace(/`([^`]+)`/g, "$1").replace(/\*([^*\n]+)\*/g, "$1");
    return {value:value.slice(0, start) + plain + value.slice(end), start, end:start + plain.length};
  }
  if (action === "link") {
    if (!/^(https?:\/\/|mailto:|tg:\/\/|\/)/i.test(url.trim())) throw new Error("Укажите ссылку, начинающуюся с https://, http://, mailto:, tg:// или /");
    if (/^https?:\/\//i.test(url.trim())) {
      try { if (!new URL(url.trim()).hostname) throw new Error(); }
      catch { throw new Error("Укажите полный адрес ссылки, например https://example.com"); }
    }
    selected ||= "ссылка";
    const target = url.trim().replace(/\(/g, "%28").replace(/\)/g, "%29").replace(/ /g, "%20");
    return {value:`${value.slice(0, start)}[${selected}](${target})${value.slice(end)}`, start:start + 1, end:start + 1 + selected.length};
  }
  const marker = MARKERS[action];
  if (!marker) return {value, start, end};
  const wrappedStars = Math.min(selected.match(/^\*+/)?.[0].length || 0, selected.match(/\*+$/)?.[0].length || 0);
  const outerStars = Math.min(value.slice(0, start).match(/\*+$/)?.[0].length || 0, value.slice(end).match(/^\*+/)?.[0].length || 0);
  const active = (stars) => action === "italic" ? stars % 2 === 1 : action === "bold" ? stars >= 2 : true;
  if (selected.startsWith(marker) && selected.endsWith(marker) && selected.length > marker.length * 2 && active(wrappedStars)) {
    const content = selected.slice(marker.length, -marker.length);
    return {value:value.slice(0, start) + content + value.slice(end), start, end:start + content.length};
  }
  if (value.slice(Math.max(0, start - marker.length), start) === marker && value.slice(end, end + marker.length) === marker && active(outerStars)) {
    return {value:value.slice(0, start - marker.length) + selected + value.slice(end + marker.length), start:start - marker.length, end:end - marker.length};
  }
  const leading = selected.match(/^\s*/)?.[0] || "";
  const trailing = selected.trim() ? selected.match(/\s*$/)?.[0] || "" : "";
  const content = selected.trim() || "текст";
  const changed = `${leading}${marker}${content}${marker}${trailing}`;
  return {value:value.slice(0, start) + changed + value.slice(end), start:start + leading.length + marker.length, end:start + leading.length + marker.length + content.length};
}

export function cellText(cell) { return String(cell?.text ?? cell ?? ""); }
export function rowCells(row) { return row?.cells || (Array.isArray(row) ? row : []); }
export function tableWidth(rows) { return Math.max(1, ...rows.map((row) => rowCells(row).length)); }

export function updateTableCell(rows, rowIndex, columnIndex, text) {
  const next = [...rows];
  while (next.length <= rowIndex) next.push({cells:[]});
  const row = next[rowIndex], cells = [...rowCells(row)];
  while (cells.length <= columnIndex) cells.push("");
  const previous = cells[columnIndex];
  cells[columnIndex] = previous && typeof previous === "object" ? {...previous, text} : text;
  next[rowIndex] = Array.isArray(row) ? cells : {...row, cells};
  return next;
}

export function changeTableColumn(rows, index, remove = false) {
  const width = tableWidth(rows);
  if (remove && width <= 1) return rows;
  return rows.map((row) => {
    const cells = [...rowCells(row)];
    while (cells.length < width) cells.push("");
    cells.splice(index, remove ? 1 : 0, ...(remove ? [] : [""]));
    return Array.isArray(row) ? cells : {...row, cells};
  });
}

export function serializeTable(rows) {
  return rows.map((row) => rowCells(row).map((cell) => cellText(cell).replace(/\\/g, "\\\\").replace(/\|/g, "\\|").replace(/\n/g, "\\n")).join(" | ")).join("\n");
}

export function parseTable(source) {
  return source.replace(/\r/g, "").split("\n").map((row) => {
    const cells = []; let value = "";
    for (let index = 0; index < row.length; index++) {
      const character = row[index];
      if (character === "\\" && ["\\", "|", "n"].includes(row[index + 1])) {
        const next = row[++index]; value += next === "n" ? "\n" : next;
      } else if (character === "|") { cells.push(value.trim()); value = ""; }
      else value += character;
    }
    cells.push(value.trim());
    return {cells};
  });
}

export function parseClipboardTable(source) {
  const rows = []; let row = [], cell = "", quoted = false;
  const input = source.replace(/\r\n/g, "\n");
  for (let index = 0; index < input.length; index++) {
    const char = input[index];
    if (char === '"' && (quoted || cell === "")) {
      if (quoted && input[index + 1] === '"') { cell += '"'; index++; }
      else quoted = !quoted;
    } else if (!quoted && (char === "\t" || char === "\n")) {
      row.push(cell); cell = "";
      if (char === "\n") { rows.push(row); row = []; }
    } else cell += char;
  }
  row.push(cell);
  if (row.length > 1 || row[0] !== "" || !rows.length) rows.push(row);
  return rows;
}

export function pasteTableCells(rows, startRow, startColumn, matrix) {
  let next = rows;
  matrix.forEach((row, r) => row.forEach((text, c) => { next = updateTableCell(next, startRow + r, startColumn + c, text); }));
  return next;
}

export function columnName(index) {
  let result = "";
  for (let value = index + 1; value > 0; value = Math.floor((value - 1) / 26)) result = String.fromCharCode(65 + (value - 1) % 26) + result;
  return result;
}
