from .base import BaseParser, ParsedItem

alph_caps = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


class CapsParser(BaseParser):
    """Заглавные буквы → '_'. Заглавные буквы строчными уходят в correct_options."""

    def parse_one(self, raw: str) -> ParsedItem:
        correct_options = []
        visible, correct = "", ""
        for letter in raw:
            if letter in alph_caps:
                correct_options.append(letter.lower())
                visible += "_"
                correct += letter
            else:
                visible += letter
                correct += letter
        return ParsedItem(
            content_raw=raw,
            content_visible=visible,
            content_correct=correct,
            correct_options=correct_options,
        )
