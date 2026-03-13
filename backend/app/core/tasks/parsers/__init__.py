# app/core/tasks/parsers/__init__.py

from .base import ParsedItem, BaseParser, VOWELS_RU
from .registry import get_parser, PARSERS

__all__ = ["ParsedItem", "BaseParser", "VOWELS_RU", "get_parser", "PARSERS"]
