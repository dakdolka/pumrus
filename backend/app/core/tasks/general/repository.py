from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .entities import Task, TaskItem, OptionSet, Option, TaskGroup


class ITaskRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]: ...

    @abstractmethod
    async def get_all_by_group(self, session: AsyncSession, group_id: int) -> List[Task]: ...

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[Task]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, name: str, group_id: int,
                     default_option_set_id: Optional[int]) -> Task: ...

    @abstractmethod
    async def update(self, session: AsyncSession, task_id: int, name: Optional[str],
                     group_id: Optional[int], default_option_set_id: Optional[int]) -> Task: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, task_id: int) -> None: ...


class ITaskItemRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, item_id: int) -> Optional[TaskItem]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, task_id: int, content_raw: str,
                     content_visible: str, content_correct: str,
                     correct_option_id: Optional[int],
                     option_set_override_id: Optional[int],
                     notice_wrong: Optional[str],
                     notice_right: Optional[str]) -> TaskItem: ...

    @abstractmethod
    async def update(self, session: AsyncSession, item_id: int,
                     content_raw: Optional[str], content_visible: Optional[str],
                     content_correct: Optional[str], correct_option_id: Optional[int],
                     option_set_override_id: Optional[int],
                     notice_wrong: Optional[str], notice_right: Optional[str]) -> TaskItem: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, item_id: int) -> None: ...


class IOptionSetRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, set_id: int) -> Optional[OptionSet]: ...

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[OptionSet]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, name: str,
                     option_ids: List[int]) -> OptionSet: ...

    @abstractmethod
    async def update(self, session: AsyncSession, set_id: int,
                     name: Optional[str], option_ids: Optional[List[int]]) -> OptionSet: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, set_id: int) -> None: ...


class IOptionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, option_id: int) -> Optional[Option]: ...

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[Option]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, content: str,
                     extras: Optional[str]) -> Option: ...

    @abstractmethod
    async def update(self, session: AsyncSession, option_id: int,
                     content: Optional[str], extras: Optional[str]) -> Option: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, option_id: int) -> None: ...


class ITaskGroupRepository(ABC):

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> List[TaskGroup]: ...

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, group_id: int) -> Optional[TaskGroup]: ...

    @abstractmethod
    async def create(self, session: AsyncSession, name: str) -> TaskGroup: ...

    @abstractmethod
    async def update(self, session: AsyncSession, group_id: int, name: str) -> TaskGroup: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, group_id: int) -> None: ...
