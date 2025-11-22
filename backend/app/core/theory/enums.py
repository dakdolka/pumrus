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

class TheoryType(str, Enum):
    speechpart = "speechpart"
    text = "text"
    wordparts = "wordparts"
    punctuation = "punctuation"
