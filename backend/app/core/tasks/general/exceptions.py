class OptionSetMissingError(Exception):
    """TaskItem не имеет ни option_set_override, ни default_option_set у Task"""
    pass


class TaskNotFoundError(Exception):
    pass


class TaskItemNotFoundError(Exception):
    pass


class OptionSetNotFoundError(Exception):
    pass


class OptionNotFoundError(Exception):
    pass


class TaskGroupNotFoundError(Exception):
    pass
