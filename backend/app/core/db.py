from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String
from app.core.config import settings
from typing import Annotated
from sqlalchemy.orm import declared_attr, DeclarativeBase
from sqlalchemy import DateTime, func
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
# асинхронный движоек
async_engine = create_async_engine(
    url=settings.db_url,
    echo=False,  # выключение логов
    pool_size=5,
    max_overflow=10,
)

# как бы исполнитель запросов
async_session_factory = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# дополнительный класс данных для бд
str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    # добавляем аннотации
    type_annotation_map = {
        str_256: String(256),
    }

    repr_columns_num = 200
    repr_cols = tuple()

    def __repr__(self):  # переделка принта моделей в логах
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_columns_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"==== {self.__class__.__name__} {', '.join(cols)} ===="

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


async def get_db():
    async with async_session_factory() as session:
        yield session
