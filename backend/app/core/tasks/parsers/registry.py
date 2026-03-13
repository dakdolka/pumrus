from .caps import CapsParser
from .custom_4 import Custom4Parser
from .custom_14 import SpellingParser
from .base import BaseParser

PARSERS: dict[str, BaseParser] = {
    "caps":     CapsParser(),    # заглавная → пропуск (ударения, орфография)
    "custom_4": Custom4Parser(), # заглавная → строчная (ПРЕ/ПРИ)
    "custom_14": SpellingParser(), # слитно/раздельно/дефис
}


def get_parser(parser_type: str) -> BaseParser:
    parser = PARSERS.get(parser_type)
    if not parser:
        available = ", ".join(PARSERS.keys())
        raise ValueError(
            f"Неизвестный тип парсера '{parser_type}'. Доступные: {available}"
        )
    return parser
