import asyncio
import logging
import sys
from logging.config import fileConfig

from utils import logger
from loguru import logger as log
import inspect

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from alembic import context


from model import schemas

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Setup basic logger for alembic (before loading full settings)
logger.setup_basic_logger()

# Setup the custom logger
logger.intercept_logger("sqlalchemy", level=logging.INFO)
logger.intercept_logger("alembic", level=logging.INFO)
logger.set_colors()


# log the name of each schemas imported
for name, obj in inspect.getmembers(schemas, inspect.isclass):
    if obj.__module__ == schemas.__name__:
        log.info(f"Imported schema: {name}")

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def process_revision_directives(context, revision, directives):
    script = directives[0]
    if script.upgrade_ops.is_empty():
        # print("Aucun changement de schéma détecté - Aucun fichier de migration ne sera créé")
        directives[:] = []


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    from utils.settings import EnvSettings

    try:
        env = EnvSettings()  # type: ignore[call-arg]
        url = f"{env.postgres_scheme}://{env.postgres_user}:{env.postgres_password}@{env.postgres_host}:{env.postgres_port}/{env.postgres_db}"
    except Exception as e:
        log.error(f"Failed to load database configuration from .env: {e}")
        sys.exit(1)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Ajouter cette ligne pour utiliser la fonction de traitement
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from utils.settings import EnvSettings

    try:
        env = EnvSettings()  # type: ignore[call-arg]
        url = f"{env.postgres_scheme}://{env.postgres_user}:{env.postgres_password}@{env.postgres_host}:{env.postgres_port}/{env.postgres_db}"
    except Exception as e:
        log.error(f"Failed to load database configuration from .env: {e}")
        sys.exit(1)

    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
