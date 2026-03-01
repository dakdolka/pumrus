from typing import Any, Iterable, List

from .entities import TaskItem
from .enums import TrainerType


def parse_words_with_capitals(
    task_id: int,
    trainer_type: TrainerType,
    raw_words: Iterable[str],
) -> List[TaskItem]:
    """
    Общий парсер для тренажёров, где raw = 'слОво' с заглавными буквами
    (ударения, ПРЕ/ПРИ, словарные).
    Один TaskItem = одна заглавная буква.
    """
    items: List[TaskItem] = []
    order = 0

    for word in raw_words:
        lower = word.lower()
        for char_index, ch in enumerate(word):
            if ch == ch.lower():
                continue

            correct_char = lower[char_index]
            visible = lower
            correct_visible = lower

            items.append(
                TaskItem(
                    id=None,
                    task_id=task_id,
                    order=order,
                    trainer_type=trainer_type,
                    raw=word,
                    visible=visible,
                    correct_option=correct_char,
                    correct_visible=correct_visible,
                    extra={"char_index": char_index},
                )
            )
            order += 1

    return items


def parse_spelling_raw(task_id: int, raw_entries: Iterable[dict[str, Any]]) -> List[TaskItem]:
    """
    raw_entries: [{ "word": "в(течение) дня", "correct": "separate" | "solid" }, ...]
    """
    import re

    def resolve_word(word: str, correct: str) -> str:
        parts: list[str] = []
        regex = re.compile(r"\(([^)]+)\)")
        last_index = 0
        for m in regex.finditer(word):
            if m.start() > last_index:
                parts.append(word[last_index:m.start()])
            parts.append(m.group(1))
            last_index = m.end()
        if last_index < len(word):
            parts.append(word[last_index:])

        if correct == "separate":
            return " ".join(parts)
        return "".join(parts)

    items: List[TaskItem] = []
    for idx, entry in enumerate(raw_entries):
        word = entry["word"]
        correct = entry["correct"]  # "solid" | "separate"
        visible = word
        correct_visible = resolve_word(word, correct)

        items.append(
            TaskItem(
                id=None,
                task_id=task_id,
                order=idx,
                trainer_type=TrainerType.SPELLING,
                raw=word,
                visible=visible,
                correct_option=str(correct),
                correct_visible=correct_visible,
                extra={},
            )
        )
    return items


def parse_raw_content(
    task_id: int,
    trainer_type: TrainerType,
    raw_content: Any,
) -> List[TaskItem]:
    """
    Универсальная точка входа:
    - STRESS / PREFIX / DICTIONARY: raw_content = список строк ["прИморье", ...]
    - SPELLING: raw_content = список объектов { word, correct }
    """
    if trainer_type in (TrainerType.STRESS, TrainerType.PREFIX, TrainerType.DICTIONARY):
        return parse_words_with_capitals(task_id, trainer_type, raw_content)

    if trainer_type == TrainerType.SPELLING:
        return parse_spelling_raw(task_id, raw_content)

    raise ValueError(f"Unsupported trainer_type: {trainer_type}")
