from dataclasses import dataclass, field
from typing import List, Optional
from .exceptions import OptionSetMissingError


@dataclass
class Option:
    id: int
    content: str
    extras: Optional[str] = None


@dataclass
class OptionSet:
    id: int
    name: str
    options: List[Option] = field(default_factory=list)


@dataclass
class TaskGroup:
    id: int
    name: str


@dataclass
class TaskItem:
    id: int
    content_raw: str
    content_visible: str
    content_correct: str
    correct_option: Optional[Option] = None
    option_set_override: Optional[OptionSet] = None
    notice_wrong: Optional[str] = None
    notice_right: Optional[str] = None

    def resolve_option_set(self, default: Optional[OptionSet]) -> OptionSet:
        if self.option_set_override:
            return self.option_set_override
        if default:
            return default
        raise OptionSetMissingError(
            "Нигде не указан набор опций для TaskItem. "
            "Укажите option_set_override или default_option_set у Task."
        )

    def get_notice(self, chosen: Option) -> Optional[str]:
        if self.correct_option and chosen.id == self.correct_option.id:
            return self.notice_right
        return self.notice_wrong


@dataclass
class Task:
    id: int
    name: str
    group: TaskGroup
    default_option_set: Optional[OptionSet] = None
    items: List[TaskItem] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return bool(self.items)
