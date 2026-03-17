from .base import BaseParser, ParsedItem
import json

CORRECT_VALUES = {"Раздельно", "Слитно", "Дефис"}


class SpellingParser(BaseParser):
    """
    Вход: {"word": "в(течение) дня", "correct": "separate"}
    visible: "в(течение) дня"
    correct: слово с применённым правилом
    correct_options: ["separate"] | ["solid"] | ["hyphen"]
    """

    def parse_one(self, raw: str | dict) -> ParsedItem:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raise ValueError(
                    f"Ожидается dict или JSON-строка, получено: '{raw}'. "
                    f'Пример: {{"word": "в(течение) дня", "correct": "separate"}}'
                )

        if not isinstance(raw, dict):
            raise ValueError(f"Элемент должен быть dict, получено: {type(raw)}")

        word = raw.get("word", "").strip()
        correct = raw.get("correct", "").strip()

        if not word:
            raise ValueError("Поле 'word' обязательно")

        if correct not in CORRECT_VALUES:
            raise ValueError(
                f"Поле 'correct' должно быть одним из {CORRECT_VALUES}, получено: '{correct}'"
            )

        if correct == "Раздельно":
            content_correct = word.replace("(", "").replace(")", " ").strip()
        elif correct == "Слитно":
            content_correct = word.replace("(", "").replace(")", "")
        else:  # hyphen
            content_correct = word.replace("(", "").replace(")", "-")

        return ParsedItem(
            content_raw=str(raw),
            content_visible=word,
            content_correct=content_correct,
            correct_options=[correct],
        )
