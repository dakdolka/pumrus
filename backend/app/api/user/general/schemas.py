from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tg_id: str
    name: str
    second_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: bool
    is_admin: bool
    last_active_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UserGetOrCreateIn(BaseModel):
    tg_id: str
    name: str
    second_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdateIn(BaseModel):
    name: Optional[str] = None
    second_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class UserGetOrCreateOut(BaseModel):
    user: UserOut
    created: bool  # True = новый, False = уже существовал
