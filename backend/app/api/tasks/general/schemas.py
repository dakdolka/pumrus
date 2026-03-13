from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any


class TaskGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class TaskGroupCreateIn(BaseModel):
    name: str


class TaskGroupUpdateIn(BaseModel):
    name: str


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    extras: Optional[str] = None


class OptionGetOrCreateOut(BaseModel):
    option: OptionOut
    created: bool


class OptionCreateIn(BaseModel):
    content: str
    extras: Optional[str] = None


class OptionUpdateIn(BaseModel):
    content: Optional[str] = None
    extras: Optional[str] = None


class OptionSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    options: List[OptionOut] = []


class OptionSetCreateIn(BaseModel):
    name: str
    option_ids: List[int]


class OptionSetUpdateIn(BaseModel):
    name: Optional[str] = None
    option_ids: Optional[List[int]] = None


class TaskItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content_raw: str
    content_visible: str
    content_correct: str
    task_id: Optional[int] = None
    correct_option_id: Optional[int] = None
    option_set_override_id: Optional[int] = None
    notice_wrong: Optional[str] = None
    notice_right: Optional[str] = None
    correct_option: Optional[OptionOut] = None
    option_set_override: Optional[OptionSetOut] = None


class TaskItemCreateIn(BaseModel):
    content_raw: str
    content_visible: str
    content_correct: str
    correct_option_id: Optional[int] = None
    option_set_override_id: Optional[int] = None
    notice_wrong: Optional[str] = None
    notice_right: Optional[str] = None


class TaskItemUpdateIn(BaseModel):
    content_raw: Optional[str] = None
    content_visible: Optional[str] = None
    content_correct: Optional[str] = None
    correct_option_id: Optional[int] = None
    option_set_override_id: Optional[int] = None
    notice_wrong: Optional[str] = None
    notice_right: Optional[str] = None


class TaskItemBulkUpdateIn(BaseModel):
    id: int
    content_raw: Optional[str] = None
    content_visible: Optional[str] = None
    content_correct: Optional[str] = None
    correct_option_id: Optional[int] = None
    option_set_override_id: Optional[int] = None
    notice_wrong: Optional[str] = None
    notice_right: Optional[str] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    task_group_id: Optional[int] = None
    default_option_set_id: Optional[int] = None
    task_group: Optional[TaskGroupOut] = None
    default_option_set: Optional[OptionSetOut] = None
    items: List[TaskItemOut] = []


class TaskCreateIn(BaseModel):
    name: str
    task_group_id: Optional[int] = None
    default_option_set_id: Optional[int] = None


class TaskUpdateIn(BaseModel):
    name: Optional[str] = None
    task_group_id: Optional[int] = None
    default_option_set_id: Optional[int] = None


class ParseRawIn(BaseModel):
    parser_type: str
    raw_items: List[Any]
    option_set_id: Optional[int] = None


class ParsedItemOut(BaseModel):
    content_raw: str
    content_visible: str
    content_correct: str
    correct_options: List[str]
    correct_option_id: Optional[int] = None
