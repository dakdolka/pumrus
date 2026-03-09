from enum import Enum

class BlockType(str, Enum):
    title = "title"
    subtitle = "subtitle"
    rule = "rule"
    example = "example"
    exception = "exception"
    important = "important"
    text = "text"
    svg = "svg"
    group = "group"
    link = "link"
    note = "note"

class TheoryType(str, Enum):
    speechpart = "Части речи"
    text = "Текст"
    wordparts = "Морфемы"
    punctuation = "Пунктуация"