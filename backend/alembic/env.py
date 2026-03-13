from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подтягиваем URL из settings и прописываем в alembic config
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.db_url)

from app.core.db import Base
import app.infra.tasks.general
import app.infra.tasks.sessions
import app.infra.user.general
import app.infra.user.mistakes
import app.infra.theory

target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():  # ← синхронный, внутри run_sync
        context.run_migrations()


async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)  # ← context здесь синхронный
    await connectable.dispose()


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
