import assert from "node:assert/strict";
import test from "node:test";
import { changeTableColumn, columnName, formatSelection, parseClipboardTable, parseTable, pasteTableCells, serializeTable, updateTableCell } from "../src/form/editorTools.js";

test("formatting keeps the selected text selected and toggles cleanly", () => {
  const result = formatSelection("Перед словом после", 6, 12, "bold");
  assert.equal(result.value, "Перед **словом** после");
  assert.equal(result.value.slice(result.start, result.end), "словом");
  const undone = formatSelection(result.value, result.start, result.end, "bold");
  assert.equal(undone.value, "Перед словом после");
});

test("bold and italic combine without accidentally removing bold", () => {
  const bold = formatSelection("корень", 0, 6, "bold");
  const both = formatSelection(bold.value, bold.start, bold.end, "italic");
  assert.equal(both.value, "***корень***");
  const justBold = formatSelection(both.value, both.start, both.end, "italic");
  assert.equal(justBold.value, "**корень**");
  const justItalic = formatSelection(both.value, both.start, both.end, "bold");
  assert.equal(justItalic.value, "*корень*");
});

test("formatting preserves surrounding spaces and operates on a word at the caret", () => {
  assert.equal(formatSelection(" одно два ", 0, 10, "bold").value, " **одно два** ");
  assert.equal(formatSelection("первое слово", 9, 9, "italic").value, "первое *слово*");
});

test("list formatting covers complete selected lines and can be removed", () => {
  const numbered = formatSelection("один\nдва\nтри", 0, 8, "number");
  assert.equal(numbered.value, "1. один\n2. два\nтри");
  assert.equal(formatSelection(numbered.value, numbered.start, numbered.end, "number").value, "один\nдва\nтри");
});

test("links reject executable URLs and preserve punctuation in safe addresses", () => {
  assert.throws(() => formatSelection("правило", 0, 7, "link", "javascript:alert(1)"), /Укажите ссылку/);
  assert.throws(() => formatSelection("правило", 0, 7, "link", "https://"), /полный адрес/);
  assert.equal(formatSelection("правило", 0, 7, "link", "https://example.com/(rule)").value, "[правило](https://example.com/%28rule%29)");
});

test("a single cell edit preserves row and cell metadata and other cells", () => {
  const rows = [{note:"row",cells:[{text:"До",color:"blue"},"Другое"]}];
  const next = updateTableCell(rows, 0, 0, "После");
  assert.deepEqual(next, [{note:"row",cells:[{text:"После",color:"blue"},"Другое"]}]);
  assert.equal(rows[0].cells[0].text,"До");
});

test("source mode round-trips pipes, line breaks, backslashes and empty cells", () => {
  const rows = [{cells:["а | б", "первая\nвторая", String.raw`C:\folder\name`, ""]}, {cells:["", "дальше"]}];
  assert.deepEqual(parseTable(serializeTable(rows)), rows);
  assert.deepEqual(parseTable("заголовок    | другой"),[{cells:["заголовок","другой"]}]);
});

test("pasting an Excel range handles quoted multiline cells and escaped quotes", () => {
  const matrix = parseClipboardTable('"две\nстроки"\t"слово ""в кавычках"""\r\nниз\tконец\r\n');
  assert.deepEqual(matrix, [["две\nстроки", 'слово "в кавычках"'], ["низ", "конец"]]);
  const rows = pasteTableCells([{cells:["сохранить"]}], 1, 1, matrix);
  assert.equal(rows[0].cells[0],"сохранить");
  assert.deepEqual(rows[1].cells,["","две\nстроки",'слово "в кавычках"']);
});

test("column edits preserve content and metadata; spreadsheet labels extend past Z", () => {
  const rows = [{id:"row",cells:["А","Б"]}];
  const added = changeTableColumn(rows,1);
  assert.deepEqual(added,[{id:"row",cells:["А","","Б"]}]);
  assert.deepEqual(changeTableColumn(added,1,true),rows);
  assert.equal(columnName(25),"Z");
  assert.equal(columnName(26),"AA");
});
