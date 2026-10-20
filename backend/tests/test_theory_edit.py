import unittest
from copy import deepcopy

from app.api.v2.theory_edit import (
    EditPage, TheoryEditPackage, check_base, fingerprint, flatten_page, make_package, tree_blocks,
)
from app.scripts.add_task9_homonymy import baseline_blocks
from app.scripts.task9_homonymy import plan_patch


def page():
    return {"title": "Чередование", "ownerTitle": "Чередующиеся корни", "description": "", "blocks": tree_blocks(baseline_blocks())}


class TheoryEditTests(unittest.TestCase):
    def test_roundtrip_and_fingerprint_ignore_object_key_order(self):
        original = page()
        package = TheoryEditPackage.model_validate(make_package(1, 2, original))
        check_base(package, 1, 2, original)
        self.assertEqual(fingerprint(original), fingerprint(package.before))
        shuffled = dict(reversed(list(original.items())))
        self.assertEqual(fingerprint(original), fingerprint(shuffled))
        # Empty children/default settings do not create artificial changes.
        explicit = deepcopy(original)
        explicit["blocks"][0]["children"] = []
        self.assertEqual(fingerprint(original), fingerprint(explicit))

    def test_wrong_document_stale_version_and_changed_owner_are_rejected(self):
        original = page()
        package = TheoryEditPackage.model_validate(make_package(1, 2, original))
        with self.assertRaisesRegex(ValueError, "другой темы"):
            check_base(package, 3, 2, original)
        with self.assertRaisesRegex(ValueError, "после экспорта"):
            check_base(package, 1, 3, original)
        modified = deepcopy(original)
        modified["ownerTitle"] = "Изменение из другой вкладки"
        with self.assertRaisesRegex(ValueError, "после экспорта"):
            check_base(package, 1, 2, modified)

    def test_before_must_not_be_edited(self):
        original = page()
        package = TheoryEditPackage.model_validate(make_package(1, 2, original))
        package.before.title = "Неверный исходник"
        with self.assertRaisesRegex(ValueError, "before изменён"):
            check_base(package, 1, 2, original)

    def test_first_example_is_exactly_the_existing_additive_plan(self):
        before = baseline_blocks()
        after, _ = plan_patch(before)
        definition = {**page(), "blocks": tree_blocks(after)}
        flat = flatten_page(EditPage.model_validate(definition))
        self.assertEqual(len(flat), len(after))
        self.assertEqual(sum(b["block_type"] == "section" for b in flat), 4)
        self.assertTrue(all(b["parent_client_id"] is None or b["parent_client_id"] in {b["client_id"] for b in flat} for b in flat))

    def test_duplicate_ids_and_malformed_cells_are_rejected(self):
        definition = page()
        definition["blocks"][1]["id"] = definition["blocks"][0]["id"]
        with self.assertRaisesRegex(ValueError, "Повторяется id"):
            flatten_page(EditPage.model_validate(definition))
        definition = page()
        table = next(b for b in definition["blocks"] if b["type"] == "table")
        table["data"]["rows"] = [{"cells": "Это не список"}]
        with self.assertRaisesRegex(ValueError, "cells"):
            flatten_page(EditPage.model_validate(definition))

    def test_new_blocks_get_unique_client_ids(self):
        definition = page()
        definition["blocks"].append({"type": "rich_text", "data": {"markdown": "Новое"}})
        flat = flatten_page(EditPage.model_validate(definition))
        self.assertTrue(flat[-1]["client_id"].startswith("new:auto:"))
        self.assertEqual(len(flat), len({b["client_id"] for b in flat}))

    def test_damaged_parent_graph_is_not_silently_exported(self):
        records = baseline_blocks()
        records[0]["parent_id"] = 9999
        with self.assertRaisesRegex(ValueError, "отсутствует"):
            tree_blocks(records)
        records[0]["parent_id"] = records[1]["id"]
        records[1]["parent_id"] = records[0]["id"]
        with self.assertRaisesRegex(ValueError, "замкнутая"):
            tree_blocks(records)


if __name__ == "__main__":
    unittest.main()
