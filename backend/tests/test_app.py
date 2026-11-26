import asyncio

import httpx2
from fastapi.testclient import TestClient

from ccap.main import app

PUBLIC_PATHS = {"/api/health", "/api/auth/{provider}/login", "/api/auth/{provider}/callback"}


async def test_health(client: httpx2.AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_docs_disabled_by_default(client: httpx2.AsyncClient) -> None:
    docs = await client.get("/docs")
    openapi = await client.get("/openapi.json")

    assert (docs.status_code, openapi.status_code) == (404, 404)


async def test_every_non_public_endpoint_requires_session(client: httpx2.AsyncClient) -> None:
    # El esquema OpenAPI lista todas las rutas, aunque /openapi.json esté apagado.
    paths = {p: ops for p, ops in app.openapi()["paths"].items() if p not in PUBLIC_PATHS}

    statuses = {
        (method, path): (await client.request(method, path)).status_code
        for path, operations in paths.items()
        for method in operations
    }

    assert paths, "debería haber endpoints protegidos"
    assert set(statuses.values()) == {401}, statuses


def test_lifespan_connects_app_to_database() -> None:
    # Sin el override de los otros tests: usa el engine real que crea el lifespan.
    # psycopg async exige el SelectorEventLoop (en Windows el default es Proactor).
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as client:
        response = client.get("/api/auth/me", headers={"Cookie": "ccap_session=inventada"})

    assert response.status_code == 401
