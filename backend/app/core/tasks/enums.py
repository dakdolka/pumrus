from enum import Enum


class TrainerType(str, Enum):
    STRESS = "stress"          # орфоэпия (ударения)
    PREFIX = "prefix"          # ПРЕ/ПРИ
    DICTIONARY = "dictionary"  # словарные слова
    SPELLING = "spelling"      # слитно/раздельно


class InputMode(str, Enum):
    LETTER_BY_LETTER = "letter_by_letter"
    WHOLE_WORD_CHOICE = "whole_word_choice"
    CLICK_VOWEL = "click_vowel"
    KEYBOARD = "keyboard"
