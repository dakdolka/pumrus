from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings


async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256),
    }

    repr_columns_num = 200
    repr_cols = tuple()

    def __repr__(self):
        columns = []
        for index, column in enumerate(self.__table__.columns.keys()):
            if column in self.repr_cols or index < self.repr_columns_num:
                columns.append(f"{column}={getattr(self, column)}")
        return f"==== {self.__class__.__name__} {', '.join(columns)} ===="


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def get_db():
    async with async_session_factory() as session:
        yield session
