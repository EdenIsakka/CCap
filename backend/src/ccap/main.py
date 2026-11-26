from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from ccap.settings import Settings

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.engine = create_async_engine(settings.database_url)
    yield
    await app.state.engine.dispose()


# /docs y /openapi.json solo en desarrollo (STRIDE E-02).
app = FastAPI(
    title="CCap",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.debug else None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
