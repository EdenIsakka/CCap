import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from ccap.models import Base
from ccap.settings import DatabaseSettings

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations() -> None:
    engine = create_async_engine(DatabaseSettings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


# psycopg async no funciona con el ProactorEventLoop, el de Windows por defecto.
asyncio.run(run_migrations(), loop_factory=asyncio.SelectorEventLoop)
