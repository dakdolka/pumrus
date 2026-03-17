from app.core.tasks.general.entities import Task, TaskItem, Option, OptionSet, TaskGroup
from app.infra.tasks.general.models import TaskBD, TaskItemBD, OptionBD, OptionSetBD, TaskGroupBD


def map_option(m: OptionBD) -> Option:
    return Option(id=m.id, content=m.content, extras=m.extras)


def map_option_set(m: OptionSetBD) -> OptionSet:
    return OptionSet(
        id=m.id,
        name=m.name,
        options=[map_option(o) for o in m.options],
    )


def map_task_group(m: TaskGroupBD) -> TaskGroup:
    return TaskGroup(id=m.id, name=m.name)


def map_task_item(m: TaskItemBD) -> TaskItem:
    return TaskItem(
        id=m.id,
        task_id=m.task_id,
        content_raw=m.content_raw,
        content_visible=m.content_visible,
        content_correct=m.content_correct,
        correct_option=map_option(m.correct_option) if m.correct_option else None,
        option_set_override=map_option_set(m.option_set_override) if m.option_set_override else None,
        notice_wrong=m.notice_wrong,
        notice_right=m.notice_right,
    )


def map_task(m: TaskBD) -> Task:
    return Task(
        id=m.id,
        name=m.name,
        trainer_type=m.trainer_type,
        group=map_task_group(m.task_group) if m.task_group else None,
        default_option_set=map_option_set(m.default_option_set) if m.default_option_set else None,
        items=[map_task_item(i) for i in m.items],
    )
