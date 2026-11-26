import asyncio
import os
from collections.abc import AsyncIterator, Mapping
from pathlib import Path

import httpx2
import pytest
from alembic import command
from alembic.config import Config
from pytest_asyncio.plugin import LoopFactory
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.community.postgres import PostgresContainer

_postgres = PostgresContainer("postgres:17-alpine", driver="psycopg")


APP_URL = "http://localhost:5173"
ALLOWED_EMAIL = "persona@example.com"


def pytest_configure(config: pytest.Config) -> None:
    # Antes de recolectar los tests: ccap.main lee la configuración al importarse.
    # Valores de prueba; pisan los del .env local.
    os.environ.update(
        DEBUG="false",
        APP_URL=APP_URL,
        SESSION_SECRET="s" * 32,
        ALLOWED_EMAILS=ALLOWED_EMAIL,
        GOOGLE_CLIENT_ID="ccap-test-client",
        GOOGLE_CLIENT_SECRET="ccap-test-secret",
    )
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


@pytest.fixture
async def client(db: AsyncSession) -> AsyncIterator[httpx2.AsyncClient]:
    """Cliente HTTP contra la app, con la sesión de base de datos del test.

    https: las cookies son Secure y el cliente no las devolvería por http.
    """
    from ccap.db import get_session
    from ccap.main import app

    app.dependency_overrides[get_session] = lambda: db
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as client:
        yield client
    app.dependency_overrides.clear()
