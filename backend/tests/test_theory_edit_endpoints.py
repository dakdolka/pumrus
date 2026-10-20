import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.v2 import admin_router
from app.api.v2.theory_edit import TheoryEditPackage, make_package
from app.infra.catalog.models import TopicBD
from app.infra.content.models import TheoryDocumentBD
from tests.test_theory_edit import page


def complete(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as done:
        return done.value
    finally:
        coroutine.close()
    raise AssertionError("Unexpected I/O in the recording session")


class TheoryEditEndpointTests(unittest.TestCase):
    def setup_case(self, *, version=20, draft=None):
        self.current = page()
        self.body = TheoryEditPackage.model_validate(make_package(10, 20, self.current))
        self.body.after.blocks[0].data["markdown"] = "Дополненное правило"
        self.document = TheoryDocumentBD(id=10, topic_id=9, title=self.current["title"], published_version_id=version)
        self.owner = TopicBD(id=9, title=self.current["ownerTitle"], code="legacy-theory-9", course_version_id=1)
        self.session = MagicMock()
        self.session.scalar = AsyncMock(side_effect=[self.document, self.owner, draft])

    def test_valid_package_uses_existing_versioned_publisher(self):
        self.setup_case()
        publisher = AsyncMock(return_value={"id": 10, "publishedVersionId": 21})
        snapshot = AsyncMock(return_value=(self.owner, [], self.current))
        with patch.object(admin_router, "_edit_package_snapshot", snapshot), patch.object(admin_router, "publish_live_document", publisher):
            saved = complete(admin_router.apply_edit_package(10, self.body, self.session))
        self.assertEqual(saved["publishedVersionId"], 21)
        publisher.assert_awaited_once()
        payload = publisher.call_args.args[1]
        self.assertEqual(payload.blocks[0].data["markdown"], "Дополненное правило")
        self.assertFalse(any(b.parent_client_id for b in payload.blocks))
        self.assertTrue(all("FOR UPDATE" in str(call.args[0]) for call in self.session.scalar.call_args_list[:2]))

    def test_stale_package_does_not_reach_publisher(self):
        self.setup_case(version=21)
        publisher = AsyncMock()
        with patch.object(admin_router, "_edit_package_snapshot", AsyncMock(return_value=(self.owner, [], self.current))), patch.object(admin_router, "publish_live_document", publisher):
            with self.assertRaises(HTTPException) as caught:
                complete(admin_router.apply_edit_package(10, self.body, self.session))
        self.assertEqual(caught.exception.status_code, 409)
        self.assertIn("после экспорта", caught.exception.detail)
        publisher.assert_not_awaited()

    def test_existing_draft_and_no_changes_do_not_publish(self):
        for draft, change in [(30, True), (None, False)]:
            with self.subTest(draft=draft):
                self.setup_case(draft=draft)
                if not change:
                    self.body.after = self.body.before.model_copy(deep=True)
                publisher = AsyncMock()
                with patch.object(admin_router, "_edit_package_snapshot", AsyncMock(return_value=(self.owner, [], self.current))), patch.object(admin_router, "publish_live_document", publisher):
                    with self.assertRaises(HTTPException):
                        complete(admin_router.apply_edit_package(10, self.body, self.session))
                publisher.assert_not_awaited()

    def test_export_is_read_only_and_example_requires_correct_topic(self):
        self.setup_case()
        self.session.get = AsyncMock(return_value=self.document)
        owner = SimpleNamespace(title="Другая тема", code="other")
        with patch.object(admin_router, "_edit_package_snapshot", AsyncMock(return_value=(owner, [], self.current))):
            exported = complete(admin_router.export_edit_package(10, None, self.session))
            self.assertEqual(exported["package"]["before"], exported["package"]["after"])
            with self.assertRaises(HTTPException) as caught:
                complete(admin_router.export_edit_package(10, "task9-homonymy", self.session))
        self.assertEqual(caught.exception.status_code, 400)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
