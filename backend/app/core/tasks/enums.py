from enum import Enum


class TrainerType(str, Enum):
    STRESS = "stress"             # орфоэпия
    PREFIX = "prefix"             # ПРЕ/ПРИ
    DICTIONARY = "dictionary"     # словарные слова
    SPELLING = "spelling"         # слитно/раздельно
    # сюда же потом добавишь новые типы


class InputMode(str, Enum):
    LETTER_BY_LETTER = "letter_by_letter"   # по одной букве
    WHOLE_WORD_CHOICE = "whole_word_choice" # выбор варианта
    CLICK_VOWEL = "click_vowel"             # клик по гласной
    KEYBOARD = "keyboard"
