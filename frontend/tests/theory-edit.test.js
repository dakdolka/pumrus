import assert from "node:assert/strict";
import test from "node:test";
import { editPackageBlock, parseTheoryEdit, prettyPackage } from "../src/form/theoryEdit.js";

function fixture() {
  const before = {title:"Чередование", ownerTitle:"Чередующиеся корни", description:"", blocks:[{id:"1", type:"section", data:{title:"Группа"}, children:[{id:"2", type:"callout", data:{variant:"rule", markdown:"Исходное правило"}, settings:{authorNote:"Заметка"}}]}]};
  return {format:"pumrus.theory-edit", schemaVersion:1, base:{documentId:10, publishedVersionId:20, fingerprint:"a".repeat(64)}, before, after:structuredClone(before)};
}

test("an exported page round-trips without invented changes", () => {
  const value=fixture();
  const parsed=parseTheoryEdit(prettyPackage(value), value);
  assert.equal(parsed.changed, false);
  assert.equal(parsed.blocks[1].parentId,"1");
  assert.equal(parsed.blocks[1].settings.authorNote,"Заметка");
});

test("a clicked nested block writes back to after and leaves before unchanged", () => {
  const value=fixture(), original=prettyPackage(value);
  const edited=editPackageBlock(value,"2",{data:{variant:"rule",markdown:"**Новое** правило"}});
  assert.equal(prettyPackage(value),original);
  const parsed=parseTheoryEdit(prettyPackage(edited),value);
  assert.equal(parsed.changed,true);
  assert.equal(parsed.before.blocks[1].data.markdown,"Исходное правило");
  assert.equal(parsed.after.blocks[1].data.markdown,"**Новое** правило");
  assert.equal(parsed.after.blocks[1].settings.authorNote,"Заметка");
});

test("new blocks can omit id; deleting a group removes its descendants", () => {
  const value=fixture();
  value.after.blocks.push({type:"rich_text",data:{markdown:"Новый текст"}});
  const parsed=parseTheoryEdit(prettyPackage(value),fixture());
  assert.match(parsed.blocks.at(-1).id,/^new:auto:/);
  const edited=editPackageBlock(value,"1",{},true);
  assert.equal(parseTheoryEdit(prettyPackage(edited),fixture()).blocks.length,1);
});

test("wrong topic, stale base, edited before and duplicate ids are rejected", () => {
  const value=fixture(), expected=fixture();
  value.base.documentId=99;
  assert.throws(()=>parseTheoryEdit(prettyPackage(value),expected),/другой теме/);
  value.base=expected.base;
  value.before.ownerTitle="Изменённый исходник";
  assert.throws(()=>parseTheoryEdit(prettyPackage(value),expected),/before изменён/);
  const duplicate=fixture();
  duplicate.after.blocks[0].children[0].id="1";
  assert.throws(()=>parseTheoryEdit(prettyPackage(duplicate),expected),/повторяется/);
});

test("invalid JSON, unknown fields, broken data and unknown types have readable errors", () => {
  assert.throws(()=>parseTheoryEdit("<script>alert(1)</script>"),/Ошибка JSON/);
  const value=fixture(); value.after.block=[];
  assert.throws(()=>parseTheoryEdit(prettyPackage(value)),/неизвестное поле/);
  const broken=fixture(); broken.after.blocks[0].children[0].data.markdown={text:"bad"};
  assert.throws(()=>parseTheoryEdit(prettyPackage(broken)),/ожидается текст/);
  broken.after.blocks[0].children[0].type="script";
  assert.throws(()=>parseTheoryEdit(prettyPackage(broken)),/неизвестный тип/);
});

test("JSON fenced by a chat response is accepted", () => {
  const value=fixture();
  assert.equal(parseTheoryEdit(`\`\`\`json\n${prettyPackage(value)}\n\`\`\``,value).changed,false);
});

test("an incomplete inspector field can be repaired while publication is blocked", () => {
  const value=fixture();
  value.after.blocks.push({type:"theory_link",data:{taskNumber:11,topicId:19}});
  const invalid=editPackageBlock(value,"new:auto:3",{data:{taskNumber:11,topicId:null}});
  assert.throws(()=>parseTheoryEdit(prettyPackage(invalid)),/taskNumber и topicId/);
  const repaired=editPackageBlock(invalid,"new:auto:3",{data:{taskNumber:11,topicId:20}});
  assert.equal(parseTheoryEdit(prettyPackage(repaired)).blocks.at(-1).data.topicId,20);
  assert.equal(value.after.blocks.at(-1).data.topicId,19);
});
