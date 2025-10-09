from types import ModuleType
from typing import TypeVar, Generic, Optional, List, Union
from sqlalchemy.orm import declarative_base, sessionmaker
from functools import wraps
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import Callable, Any
from sqlalchemy import select, DateTime, func, insert
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from core.db import Base, async_engine, async_session_factory
from models import *

async def create_all():
        async with async_engine.begin() as conn:
            async_engine.echo = False
            print(Base.metadata.tables.keys())
            await conn.run_sync(Base.metadata.drop_all) #TODO убрать в проде
            await conn.run_sync(Base.metadata.create_all)
            print('tables created')
            async_engine.echo = True