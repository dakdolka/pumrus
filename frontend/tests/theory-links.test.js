import assert from "node:assert/strict";
import test from "node:test";
import { theoryAnchorId, theoryHref } from "../src/theory/theoryLinks.js";
import { flattenEditPage } from "../src/form/theoryEdit.js";

test("theory links use stable section labels, independent of block IDs", () => {
  assert.equal(theoryHref({taskNumber:11, topicId:19, anchor:"i-y-suffix"}), "/theory/tasks/11/topics/19#theory-i-y-suffix");
  assert.equal(theoryHref({taskNumber:9, topicId:10}), "/theory/tasks/9/topics/10");
  for (const bad of [null, {}, {taskNumber:11,topicId:"19"}, {taskNumber:0,topicId:19}, {taskNumber:11,topicId:19,anchor:"../oops"}, {taskNumber:11,topicId:19,anchor:0}]) assert.equal(theoryHref(bad), "");
  assert.equal(theoryAnchorId("a".repeat(64)), `theory-${"a".repeat(64)}`);
  assert.equal(theoryAnchorId("a".repeat(65)), "");
});

test("packages reject broken navigation targets and ambiguous section labels", () => {
  const page={title:"Тема",ownerTitle:"Тема",blocks:[{type:"section",data:{title:"Продолжение"},settings:{anchor:"i-y-suffix"},children:[{type:"theory_link",data:{taskNumber:9,topicId:9,buttonLabel:"В корень"}}]}]};
  assert.equal(flattenEditPage(page).length,2);
  page.blocks[0].children[0].data.topicId=null;
  assert.throws(()=>flattenEditPage(page),/taskNumber и topicId/);
  page.blocks[0].children[0].data.topicId=9;
  page.blocks[0].children[0].settings={anchor:"i-y-suffix"};
  assert.throws(()=>flattenEditPage(page),/повторяется метка/);
});
