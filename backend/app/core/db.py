from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import String
from app.core.config import settings
from typing import Annotated

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
