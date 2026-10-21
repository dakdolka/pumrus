import json
import re
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.v2 import practice_revision
from app.api.v2.router import _public_question
from app.infra.exercises.models import ExerciseBD, ExerciseVersionBD, ExerciseSetBD, ExerciseTaskLinkBD, ExerciseTopicLinkBD
from app.scripts.curated_task10_11_practice import candidate_cards, reviewed_cards
from app.scripts.task10_11_revision import EVIDENCE, digest, legacy_lexeme, snapshot, validate_card, validate_package
from app.scripts.verify_task10_11_dictionary import headwords
from app.scripts.practice_scope_sync import _unique_word_exercise_ids, infer_topic_code
from tests.test_theory_edit_endpoints import complete


def cards():
    return reviewed_cards(json.loads(EVIDENCE.read_text(encoding="utf-8")))


def fixture():
    desired = [next(c for c in cards() if c["lexeme"] == word) for word in ["въявь", "рисовать"]]
    tasks = [{"id": n, "number": n, "courseVersionId": 1} for n in [10, 11]]
    topics = [{"id": 5, "code": "legacy-theory-7", "title": "Знаки"}, {"id": 17, "code": "legacy-theory-23", "title": "Глаголы"}]
    sets = [{"id": sid, "courseVersionId": 1, "taskId": task, "topicId": topic, "title": "Старый набор", "status": "published", "configuration": {"scopeRole": role}} for sid, task, topic, role in [(53, 10, None, "task"), (7, 11, None, "task"), (59, 11, 17, "topic"), (14, 10, None, "source")]]
    versions = [{"id": 100 + i, "exerciseId": 10 + i, "versionNumber": 1, "interactionType": "vowel_fill", "promptData": {"content": mask}, "answerConfig": {"acceptedAnswers": [word]}, "checkerConfig": {}, "feedbackData": {"correctAnswer": word}} for i, (word, mask) in enumerate([("въявь", "в_явь"), ("рисовать", "рис_вать"), ("пьявка", "п_явка")])]
    export = {"catalog": {"tasks": tasks, "topics": topics, "taskTopicLinks": [{"taskId": 10, "topicId": 5}, {"taskId": 11, "topicId": 17}]}, "practice": {
        "exerciseSets": sets, "exercises": [{"id": 10 + i, "courseVersionId": 1, "publishedVersionId": 100 + i, "status": "published"} for i in range(3)], "exerciseVersions": versions,
        "exerciseTaskLinks": [{"exerciseId": 10, "taskId": 11}, {"exerciseId": 11, "taskId": 11}, {"exerciseId": 12, "taskId": 10}],
        "exerciseTopicLinks": [{"exerciseId": 10, "topicId": 17}, {"exerciseId": 11, "topicId": 17}],
        "exerciseSetItems": [{"id": i + 1, "exerciseSetId": s, "exerciseId": e} for i, (s, e) in enumerate([(7, 10), (7, 11), (59, 10), (59, 11), (53, 12), (14, 12)])],
    }}
    before = snapshot(export)
    package = {"format": "pumrus.practice-edit", "schemaVersion": 1, "revision": "test", "base": {"taskNumbers": [10, 11], "fingerprint": digest(before)}, "before": before,
               "after": {"topics": [{"taskNumber": n, "topicId": tid, "topicCode": card["topic_code"], "title": title, "cards": [card]} for n, tid, title, card in [(10, 5, "Знаки", desired[0]), (11, 17, "Глаголы", desired[1])]]}}
    return export, package


class Task10Task11DataTests(unittest.TestCase):
    def test_dictionary_parser_handles_stress_footnotes_and_optional_reflexives(self):
        source = '<span class="title"><b><span class="marked">безграни&#x301;чный</span>*;</b></span><span class="title"><b>адресова&#769;ть(ся)</b></span>'
        self.assertEqual(headwords(source), ["адресовать", "адресоваться", "безграничный"])

    def test_every_released_card_has_real_evidence_explanation_and_valid_mask(self):
        reviewed = cards()
        self.assertGreater(len(reviewed), 1900)
        self.assertEqual(len({c["topic_code"] for c in reviewed}), 10)
        for card in reviewed:
            with self.subTest(word=card["lexeme"]):
                validate_card(card)
                self.assertGreater(len(card["explanation"]), 40)
        self.assertFalse({"изьян", "пьявка", "уменьшивать", "ускользывать", "обоснововать"} & {c["lexeme"] for c in reviewed})

    def test_no_repeated_words_or_masks_in_a_topic(self):
        words, masks = set(), set()
        for card in cards():
            key = (card["topic_code"], card["lexeme"].replace("ё", "е"))
            mask = (card["topic_code"], card["prompt"])
            self.assertNotIn(key, words); self.assertNotIn(mask, masks)
            words.add(key); masks.add(mask)

    def test_suffix_masks_target_the_suffix(self):
        for card in cards():
            positions = [i for i, c in enumerate(card["prompt"]) if c == "_"]
            if card["rule_id"] == "verb-iva":
                suffix = re.search(r"[ыи]ва(?:ть|ться)$", card["lexeme"])
                self.assertIsNotNone(suffix, card["lexeme"])
                self.assertEqual(positions, [suffix.start()], card["lexeme"])
            if card["rule_id"] in {"noun-ik", "noun-ek"}:
                self.assertEqual(positions, [len(card["lexeme"]) - 2], card["lexeme"])

    def test_ambiguous_words_have_context_and_correct_special_cases_are_present(self):
        by_word = {c["lexeme"]: c for c in cards()}
        for word in ["обезводеть", "обезводить", "претворить", "притворить", "преуменьшить", "приуменьшить", "масляный", "масленый"]:
            self.assertIn(word, by_word)
            self.assertNotEqual(by_word[word]["answer"], word)
        for word in ["разыскной", "взимать", "милостивый", "юродивый", "сестрицын", "лекция", "дословно", "лишён", "достоин"]:
            self.assertIn(word, by_word)

    def test_empty_evidence_never_falls_back_to_unchecked_candidates(self):
        self.assertEqual(reviewed_cards({}), [])
        self.assertGreater(len(candidate_cards()), len(cards()))


class PracticeRevisionPackageTests(unittest.TestCase):
    def test_sources_are_only_disclosed_after_an_answer_and_urls_are_filtered(self):
        version = SimpleNamespace(interaction_type="vowel_fill", response_schema_version=1, prompt_data={"content": "пр_творить"}, interaction_config={"mask": "пр_творить"}, answer_config={"acceptedAnswers": ["притворить"]}, checker_type="normalized_text", feedback_data={"correctAnswer": "притворить", "correct": "Написание проверено"}, checker_config={"sourceReferences": ["https://orfo.ruslang.ru/search", "javascript:alert(1)", None, "https://orfo.ruslang.ru/search"]})
        item = SimpleNamespace(id=1, position=0, state="pending")
        question = _public_question(item, version)
        self.assertIsNone(question["result"])
        self.assertNotIn("orfo.ruslang.ru", json.dumps(question))
        attempt = SimpleNamespace(id=2, result_status="correct", score=1, response_data={"text": "притворить"})
        completed = _public_question(item, version, attempt)
        self.assertEqual(completed["result"]["feedback"]["sources"], ["https://orfo.ruslang.ru/search"])

    def test_export_base_is_sensitive_to_content_but_not_export_timestamps(self):
        export, package = fixture()
        validate_package(package)
        changed = deepcopy(export)
        changed["practice"]["exerciseVersions"][0]["updatedAt"] = "later"
        self.assertEqual(digest(snapshot(changed)), package["base"]["fingerprint"])
        changed["practice"]["exerciseVersions"][0]["feedbackData"]["correct"] = "Изменение владельца"
        self.assertNotEqual(digest(snapshot(changed)), package["base"]["fingerprint"])

    def test_changed_before_broken_evidence_and_wrong_topic_are_rejected(self):
        _, package = fixture()
        for mutation in [lambda p: p["before"]["sets"].clear(), lambda p: p["after"]["topics"][0]["cards"][0]["dictionary_evidence"].update(status="not_found"), lambda p: p["after"]["topics"][0].update(topicId=999)]:
            broken = deepcopy(package); mutation(broken)
            with self.assertRaises(ValueError): validate_package(broken)

    def test_legacy_target_word_is_recovered_inside_context(self):
        row = {"promptData": {"content": "власти пр_держащие"}, "feedbackData": {"correctAnswer": "власти прЕдержащие"}}
        self.assertEqual(legacy_lexeme(row), "предержащие")

    def test_preview_and_stale_apply_never_write(self):
        export, package = fixture(); session = MagicMock()
        with patch.object(practice_revision, "build_practice_export", AsyncMock(return_value=export)):
            result = complete(practice_revision.preview(session, package))
        self.assertEqual(result["summary"]["after"]["exercises"], 2)
        session.add.assert_not_called(); session.commit.assert_not_called()
        changed = deepcopy(export); changed["practice"]["exerciseSets"][0]["title"] = "Чужая правка"
        session.scalars = AsyncMock(return_value=SimpleNamespace(all=lambda: []))
        with patch.object(practice_revision, "build_practice_export", AsyncMock(return_value=changed)):
            with self.assertRaises(HTTPException) as caught: complete(practice_revision.apply(session, package))
        self.assertEqual(caught.exception.status_code, 409)
        session.add.assert_not_called(); session.commit.assert_not_called()

    def test_publication_reuses_ids_moves_wrong_task_links_and_keeps_history(self):
        export, package = fixture(); session = MagicMock(); added = []
        exercises = [ExerciseBD(id=e["id"], course_version_id=1, published_version_id=e["publishedVersionId"], status="published") for e in package["before"]["exercises"]]
        sets = [ExerciseSetBD(id=s["id"], course_version_id=1, exam_task_id=s["taskId"], topic_id=s["topicId"], title=s["title"], status="published", configuration=s["configuration"]) for s in package["before"]["sets"]]
        versions = [ExerciseVersionBD(id=v["id"], status="published") for v in package["before"]["versions"] if v["id"] in {100, 101}]
        session.scalars = AsyncMock(side_effect=[SimpleNamespace(all=lambda: []), SimpleNamespace(all=lambda: sets), SimpleNamespace(all=lambda: exercises), SimpleNamespace(all=lambda: []), SimpleNamespace(all=lambda: versions)])
        session.scalar = AsyncMock(return_value=None)
        session.execute = AsyncMock(return_value=SimpleNamespace(all=lambda: [(10, 1), (11, 1), (12, 1)]))
        session.add_all.side_effect = lambda rows: added.extend(rows)
        session.add.side_effect = added.append
        async def flush():
            for index, item in enumerate(added, 1000):
                if hasattr(item, "id") and item.id is None: item.id = index
        session.flush = AsyncMock(side_effect=flush); session.commit = AsyncMock()
        sync = AsyncMock()
        with patch.object(practice_revision, "build_practice_export", AsyncMock(return_value=export)), patch.object(practice_revision, "_sync_membership", sync), patch.object(practice_revision, "sync_preview_membership", AsyncMock(return_value=0)):
            result = complete(practice_revision.apply(session, package))
        self.assertEqual(result["changes"]["created"], 0)
        self.assertEqual(result["changes"]["updated"], 2)
        self.assertEqual(result["changes"]["retired"], 1)
        new_versions = [v for v in added if isinstance(v, ExerciseVersionBD)]
        self.assertEqual({v.exercise_id for v in new_versions}, {10, 11})
        self.assertTrue(all(v.version_number == 2 for v in new_versions))
        links = {(v.exercise_id, v.exam_task_id) for v in added if isinstance(v, ExerciseTaskLinkBD)}
        self.assertEqual(links, {(10, 10), (11, 11)})
        self.assertTrue(any(isinstance(v, ExerciseTopicLinkBD) and v.exercise_id == 10 and v.topic_id == 5 for v in added))
        self.assertEqual(next(s for s in sets if s.id == 14).status, "archived")
        self.assertEqual(next(e for e in exercises if e.id == 12).status, "archived")
        self.assertTrue(all(v.status == "archived" for v in versions))
        session.commit.assert_awaited_once()

    def test_scope_sync_prefers_verified_cards_and_respects_explicit_topics(self):
        old = SimpleNamespace(prompt_data={"content": "пр_творить"}, answer_config={}, feedback_data={"correctAnswer": "притворить"}, checker_config={"curatedKey": "old"})
        new = SimpleNamespace(prompt_data={"content": "пр_творить дверь"}, answer_config={}, feedback_data={"correctAnswer": "притворить дверь"}, checker_config={"curatedKey": "new", "lexeme": "притворить", "dictionaryEvidence": {"status": "verified"}, "topicCode": "legacy-theory-8"})
        self.assertEqual(_unique_word_exercise_ids({1, 2}, {1: old, 2: new}), {2})
        self.assertEqual(infer_topic_code(10, new), "legacy-theory-8")


if __name__ == "__main__":
    unittest.main()
