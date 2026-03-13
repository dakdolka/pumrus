from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class User:
    id: int
    tg_id: str
    name: str
    second_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: bool = True
    is_admin: bool = False
    last_active_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
