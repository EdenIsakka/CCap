from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.middleware.sessions import SessionMiddleware

from ccap import auth
from ccap.settings import get_settings

settings = get_settings()


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
# Solo para el estado temporal del flujo OAuth. La sesión de verdad es ccap_session (ADR-0008).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="ccap_oauth",
    max_age=600,
    same_site="lax",
    https_only=True,
)

api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(auth.router)
app.include_router(api)
