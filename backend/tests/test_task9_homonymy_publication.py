"""Exercise publication boundaries with real models and a recording session."""

import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.scripts.add_task9_homonymy import baseline_blocks, run

try:
    from app.core import db
    from app.infra.catalog.models import TopicBD  # Register catalog relationships.
    from app.infra.content.models import TheoryBlockV2BD, TheoryDocumentVersionBD
    DATABASE_IMPORTS = True
except ModuleNotFoundError:
    DATABASE_IMPORTS = False


@unittest.skipUnless(DATABASE_IMPORTS, "Backend database dependencies are required")
class Task9PublicationTests(unittest.TestCase):
    def complete(self, coroutine):
        # All awaits below are immediate AsyncMocks; no sockets/event loop needed.
        try:
            coroutine.send(None)
        except StopIteration:
            return
        finally:
            coroutine.close()
        self.fail("The recording session unexpectedly performed asynchronous I/O")

    def setup_session(self, *, draft=False):
        records = baseline_blocks()
        records.append({"id": 500, "parent_id": records[2]["id"], "type": "rich_text", "data": {"markdown": "Ручная вложенность"}, "settings": {"authorNote": "Моя заметка"}, "sort_order": 0, "schema_version": 1})
        self.source = [SimpleNamespace(
            id=b["id"], parent_block_id=b["parent_id"], block_type=b["type"],
            data=b["data"], settings=b["settings"], sort_order=b["sort_order"], schema_version=1,
        ) for b in records]
        self.document = SimpleNamespace(id=10, published_version_id=20, status="published")
        responses = [[self.document], [SimpleNamespace(id=30)] if draft else [], self.source]
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        transaction = MagicMock()
        transaction.__aenter__ = AsyncMock()
        transaction.__aexit__ = AsyncMock(return_value=False)
        session.begin.return_value = transaction
        session.scalars = AsyncMock(side_effect=[SimpleNamespace(all=lambda values=values: values) for values in responses])
        session.scalar = AsyncMock(return_value=1)
        self.added = []
        session.add.side_effect = self.added.append

        async def flush():
            for index, item in enumerate(self.added, start=1000):
                if item.id is None:
                    item.id = index

        session.flush = AsyncMock(side_effect=flush)
        return session

    def test_dry_run_does_not_add_or_flush(self):
        session = self.setup_session()
        with patch.object(db, "async_session_factory", return_value=session), contextlib.redirect_stdout(io.StringIO()):
            self.complete(run("test-course", False, False))
        session.add.assert_not_called()
        session.flush.assert_not_awaited()
        self.assertEqual(self.document.published_version_id, 20)

    def test_draft_clones_content_and_remaps_all_parents(self):
        session = self.setup_session()
        with patch.object(db, "async_session_factory", return_value=session), contextlib.redirect_stdout(io.StringIO()):
            self.complete(run("test-course", True, False))
        version = next(b for b in self.added if isinstance(b, TheoryDocumentVersionBD))
        blocks = [b for b in self.added if isinstance(b, TheoryBlockV2BD)]
        ids = {b.id for b in blocks}
        self.assertEqual(version.status, "draft")
        self.assertEqual(self.document.published_version_id, 20)
        self.assertTrue(all(b.document_version_id == version.id for b in blocks))
        self.assertTrue(all(b.parent_block_id is None or b.parent_block_id in ids for b in blocks))
        manual = next(b for b in blocks if b.data.get("markdown") == "Ручная вложенность")
        self.assertEqual(manual.settings["authorNote"], "Моя заметка")
        self.assertNotEqual(manual.parent_block_id, self.source[-1].parent_block_id)
        self.assertEqual(self.source[-1].parent_block_id, 3)

    def test_publication_changes_only_pointer_after_copy(self):
        session = self.setup_session()
        with patch.object(db, "async_session_factory", return_value=session), contextlib.redirect_stdout(io.StringIO()):
            self.complete(run("test-course", True, True))
        version = next(b for b in self.added if isinstance(b, TheoryDocumentVersionBD))
        self.assertEqual(version.status, "published")
        self.assertIsNotNone(version.published_at)
        self.assertEqual(self.document.published_version_id, version.id)

    def test_existing_draft_blocks_writes(self):
        session = self.setup_session(draft=True)
        with patch.object(db, "async_session_factory", return_value=session):
            with self.assertRaisesRegex(ValueError, "Existing draft"):
                self.complete(run("test-course", True, False))
        session.add.assert_not_called()
        session.flush.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
