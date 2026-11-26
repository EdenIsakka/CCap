import asyncio
import os
from collections.abc import AsyncIterator, Mapping
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pytest_asyncio.plugin import LoopFactory
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.community.postgres import PostgresContainer

_postgres = PostgresContainer("postgres:17-alpine", driver="psycopg")


def pytest_configure(config: pytest.Config) -> None:
    # Antes de recolectar los tests: ccap.main lee DATABASE_URL al importarse.
    _postgres.start()
    # En Windows, "localhost" prueba IPv6 primero y la conexión async se cuelga.
    os.environ["DATABASE_URL"] = _postgres.get_connection_url().replace("localhost", "127.0.0.1")
    command.upgrade(Config(Path(__file__).parents[1] / "alembic.ini"), "head")


def pytest_unconfigure(config: pytest.Config) -> None:
    _postgres.stop()


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, LoopFactory]:
    # psycopg async no funciona con el ProactorEventLoop, el de Windows por defecto.
    return {"selector": asyncio.SelectorEventLoop}


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Sesión dentro de una transacción que se deshace al final: cada test parte de cero."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield session
        await session.close()
        await transaction.rollback()
