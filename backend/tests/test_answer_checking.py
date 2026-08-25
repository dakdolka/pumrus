import unittest
from types import SimpleNamespace

from app.api.v2.router import _check_answer


class AnswerCheckingTests(unittest.TestCase):
    def test_multiple_choice_partial_score(self):
        version = SimpleNamespace(
            checker_type="set_equality",
            answer_config={"correctOptionKeys": ["a", "b"]},
            checker_config={},
        )
        status, score, normalized = _check_answer(version, {"optionKeys": ["a"]})
        self.assertEqual(status, "partial")
        self.assertGreater(score, 0)
        self.assertEqual(normalized, {"optionKeys": ["a"]})

    def test_normalized_text_respects_yo_policy(self):
        version = SimpleNamespace(
            checker_type="normalized_text",
            answer_config={"acceptedAnswers": ["ёлка"]},
            checker_config={"trim": True, "caseInsensitive": True, "yoPolicy": "distinct"},
        )
        status, score, _ = _check_answer(version, {"text": "елка"})
        self.assertEqual((status, score), ("incorrect", 0.0))


if __name__ == "__main__":
    unittest.main()
