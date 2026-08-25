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
config.set_main_option("sqlalchemy.url", settings.database_url)

from app.core.db import Base
import app.infra.tasks.general
import app.infra.tasks.sessions
import app.infra.user.general
import app.infra.user.mistakes
import app.infra.theory
import app.infra.catalog
import app.infra.content
import app.infra.exercises
import app.infra.practice
import app.infra.monetization
import app.infra.system

target_metadata = Base.metadata

LEGACY_ENUM_COLUMNS = {
    ("task", "trainer_type"),
    ("theory_block", "type"),
    ("theory_type", "name"),
}


def compare_column_types(
    _context,
    inspected_column,
    metadata_column,
    _inspected_type,
    _metadata_type,
):
    """Keep legacy varchar-backed enums out of new autogeneration noise."""
    if (metadata_column.table.name, metadata_column.name) in LEGACY_ENUM_COLUMNS:
        return False
    return None


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=compare_column_types,
    )
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
