import unittest

from app.api.v2.exercise_import import parse_exercises


class ExerciseImportTests(unittest.TestCase):
    def test_vowel_fill_explicit_mask(self):
        parsed = parse_exercises("процент_ик | процентщик", "vowel_fill")
        self.assertEqual(parsed["errors"], [])
        self.assertEqual(parsed["rows"][0]["mask"], "процент_ик")
        self.assertEqual(parsed["rows"][0]["answer"], "процентщик")

    def test_single_choice_keeps_explanation(self):
        parsed = parse_exercises(
            "Он говорил (не)громко | слитно | слитно,раздельно | Нет противопоставления",
            "single_choice",
        )
        self.assertEqual(parsed["errors"], [])
        self.assertEqual(parsed["rows"][0]["answer"], "слитно")
        self.assertEqual(parsed["rows"][0]["explanation"], "Нет противопоставления")

    def test_invalid_stress_is_reported(self):
        parsed = parse_exercises("звонит", "stress_selection")
        self.assertEqual(parsed["rows"], [])
        self.assertTrue(parsed["errors"])


if __name__ == "__main__":
    unittest.main()
