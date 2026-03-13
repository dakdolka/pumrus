from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

VOWELS_RU = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")


@dataclass
class ParsedItem:
    content_raw: str
    content_visible: str
    content_correct: str
    correct_options: list[str]  # варианты ответа для отображения юзеру


class BaseParser(ABC):
    @abstractmethod
    def parse_one(self, raw: str) -> ParsedItem: ...

    def parse_many(self, raws: list) -> list[ParsedItem]:
        results = []
        for raw in raws:
            try:
                results.append(self.parse_one(raw))
            except Exception as e:
                raise ValueError(f"Ошибка парсинга '{raw}': {e}")
        return results
