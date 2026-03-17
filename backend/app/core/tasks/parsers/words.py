from .base import BaseParser, ParsedItem

alph_caps = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


class WordsParser(BaseParser):
    """Заглавные буквы → '_'. Заглавные буквы строчными уходят в correct_options."""

    def parse_one(self, raw: str) -> ParsedItem:
        visible, correct = "", ""
        for letter in raw:
            if letter in alph_caps:
                visible += "_"
                correct += letter
            else:
                visible += letter
                correct += letter
            
        return ParsedItem(
            content_raw=raw,
            content_visible=visible,
            content_correct=correct,
            correct_options=raw.lower(),
        )
