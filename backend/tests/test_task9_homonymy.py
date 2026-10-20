"""Check the additive migration's safety without a database or credentials."""

import unittest
from copy import deepcopy

from app.scripts.add_task9_homonymy import baseline_blocks
from app.scripts.task9_homonymy import HEADINGS, MARKER, REVISION, plan_patch


class Task9HomonymyTests(unittest.TestCase):
    def test_preserves_existing_content_settings_and_nested_parents(self):
        before = baseline_blocks()
        before[2]["settings"]["authorNote"] = "Авторская заметка"
        before.append({"id": 999, "parent_id": before[2]["id"], "type": "rich_text", "data": {"markdown": "Ручная правка"}, "settings": {}, "schema_version": 1, "sort_order": 0})
        original = deepcopy(before)
        after, changes = plan_patch(before)
        self.assertEqual(before, original)
        self.assertTrue(changes)
        by_id = {b["id"]: b for b in after}
        for block in before:
            self.assertEqual({k: v for k, v in block.items() if k != "sort_order"}, {k: v for k, v in by_id[block["id"]].items() if k != "sort_order"})

    def test_second_run_has_no_duplicates(self):
        after, _ = plan_patch(baseline_blocks())
        again, changes = plan_patch(after)
        self.assertEqual(after, again)
        self.assertEqual(changes, [])

    def test_partial_patch_and_changed_anchors_fail_without_mutation(self):
        after, _ = plan_patch(baseline_blocks())
        after.remove(next(b for b in after if b["settings"].get(MARKER) == REVISION))
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            plan_patch(after)
        before = baseline_blocks()
        before[1]["data"]["markdown"] = "Переименованный раздел"
        original = deepcopy(before)
        with self.assertRaisesRegex(ValueError, "anchor"):
            plan_patch(before)
        self.assertEqual(before, original)

    def test_duplicate_headings_fail(self):
        before = baseline_blocks()
        duplicate = deepcopy(next(b for b in before if b["data"].get("markdown") == HEADINGS[0]))
        duplicate["id"] = 999
        before.append(duplicate)
        with self.assertRaisesRegex(ValueError, "found 2"):
            plan_patch(before)

    def test_missing_parent_and_cycles_fail_before_planning(self):
        before = baseline_blocks()
        before[0]["parent_id"] = 9999
        with self.assertRaisesRegex(ValueError, "Missing parent"):
            plan_patch(before)
        before[0]["parent_id"] = before[1]["id"]
        before[1]["parent_id"] = before[0]["id"]
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            plan_patch(before)

    def test_sections_are_attached_and_practice_stays_last(self):
        before = baseline_blocks()
        before.append({"id": 900, "parent_id": None, "type": "practice_link", "data": {}, "settings": {}, "schema_version": 1, "sort_order": 100})
        # The same algorithm must work inside an existing outer section.
        for block in before:
            block["parent_id"] = 1000
        before.append({"id": 1000, "parent_id": None, "type": "section", "data": {"title": "Чередование"}, "settings": {}, "schema_version": 1, "sort_order": 0})
        after, _ = plan_patch(before)
        ids = {b["id"] for b in after}
        self.assertTrue(all(b["parent_id"] is None or b["parent_id"] in ids for b in after))
        siblings = sorted([b for b in after if b["parent_id"] == 1000], key=lambda b: b["sort_order"])
        self.assertEqual(siblings[-1]["id"], 900)
        self.assertEqual(sum(b["type"] == "section" for b in siblings), 4)
        self.assertTrue(all(b["parent_id"] == 1000 for b in siblings))


if __name__ == "__main__":
    unittest.main()
