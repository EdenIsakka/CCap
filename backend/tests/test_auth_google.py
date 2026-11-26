"""Login con Google (spec user-auth y security-audit).

Google se simula con un MockTransport de httpx2 (el cliente que usa authlib): sin red.
"""

import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx2
import pytest
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ccap.auth import SESSION_COOKIE, oauth
from ccap.models import AuditLog, LoginSession, User, UserIdentity
from tests.conftest import ALLOWED_EMAIL, APP_URL

ISSUER = "https://accounts.google.com"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"
TOKEN_URL = "https://oauth2.googleapis.com/token"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
CLIENT_ID = "ccap-test-client"

KEY = RSAKey.generate_key(2048, parameters={"kid": "test-key"})


class FakeGoogle:
    """Responde el descubrimiento, las llaves y el token. Cualquier otra URL falla el test."""

    def __init__(self) -> None:
        self.id_token = ""

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        if url == DISCOVERY_URL:
            return httpx2.Response(200, json=METADATA)
        if url == JWKS_URL:
            return httpx2.Response(200, json=KeySet([KEY]).as_dict(private=False))
        if url == TOKEN_URL and request.method == "POST":
            token = {"access_token": "at", "token_type": "Bearer", "id_token": self.id_token}
            return httpx2.Response(200, json=token)
        raise AssertionError(f"petición inesperada a {url}")


METADATA = {
    "issuer": ISSUER,
    "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_endpoint": TOKEN_URL,
    "jwks_uri": JWKS_URL,
    "id_token_signing_alg_values_supported": ["RS256"],
}


@pytest.fixture
def google(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeGoogle]:
    fake = FakeGoogle()
    client = oauth.create_client("google")
    monkeypatch.setitem(client.client_kwargs, "transport", httpx2.MockTransport(fake.handle))
    yield fake


def id_token(overrides: dict[str, Any]) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "sub": "google-sub-1",
        "email": ALLOWED_EMAIL,
        "email_verified": True,
        "nonce": "sin-nonce",
        "iat": now,
        "exp": now + 3600,
    } | overrides
    return jwt.encode({"alg": "RS256", "kid": "test-key"}, claims, KEY)


async def start_login(client: httpx2.AsyncClient) -> dict[str, str]:
    response = await client.get("/api/auth/google/login")
    query = parse_qs(urlsplit(response.headers["location"]).query)
    return {key: values[0] for key, values in query.items()}


async def finish_login(
    client: httpx2.AsyncClient, google: FakeGoogle, **claims: Any
) -> httpx2.Response:
    """Inicia el login y vuelve al callback con un ID token firmado por la llave de prueba."""
    params = await start_login(client)
    google.id_token = id_token({"nonce": params["nonce"]} | claims)
    return await client.get(
        "/api/auth/google/callback", params={"code": "code", "state": params["state"]}
    )


async def count(db: AsyncSession, model: type[Any]) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


async def me_with(client: httpx2.AsyncClient, token: str) -> httpx2.Response:
    """Consulta /me con un token dado, reemplazando la cookie que tenga el cliente."""
    client.cookies.clear()
    client.cookies.set(SESSION_COOKIE, token, domain="test")
    return await client.get("/api/auth/me")


# --- Redirección a Google ---


async def test_login_redirects_to_google_with_state_nonce_and_pkce(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    params = await start_login(client)

    assert params["scope"] == "openid email"
    assert params["state"] and params["nonce"] and params["code_challenge"]
    assert params["code_challenge_method"] == "S256"
    assert params["redirect_uri"] == f"{APP_URL}/api/auth/google/callback"


async def test_login_does_not_ask_for_mail_permissions(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    params = await start_login(client)

    assert "gmail" not in params["scope"] and "Mail.Read" not in params["scope"]


# --- Validación del callback ---


async def test_callback_with_other_state_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    await start_login(client)

    response = await client.get(
        "/api/auth/google/callback", params={"code": "code", "state": "otro"}
    )

    assert response.status_code == 400
    assert await count(db, LoginSession) == 0


async def test_callback_without_previous_login_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await client.get(
        "/api/auth/google/callback", params={"code": "code", "state": "inventado"}
    )

    assert response.status_code == 400
    assert await count(db, LoginSession) == 0


async def test_id_token_for_another_audience_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await finish_login(client, google, aud="otra-app")

    assert response.status_code == 400
    assert await count(db, LoginSession) == 0


async def test_id_token_with_other_nonce_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await finish_login(client, google, nonce="otro")

    assert response.status_code == 400
    assert await count(db, LoginSession) == 0


async def test_id_token_from_another_issuer_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await finish_login(client, google, iss="https://evil.example.com")

    assert response.status_code == 400
    assert await count(db, LoginSession) == 0


# --- Solo entran correos permitidos ---


async def test_allowed_email_gets_session_and_returns_to_pwa(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    response = await finish_login(client, google)

    assert response.status_code == 303
    assert response.headers["location"] == f"{APP_URL}/"
    assert SESSION_COOKIE in response.cookies


async def test_email_not_allowed_is_denied_without_session_or_user(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await finish_login(client, google, email="intrusa@example.com")

    assert response.status_code == 303
    assert response.headers["location"] == f"{APP_URL}/?login=denied"
    assert SESSION_COOKIE not in response.cookies
    assert (await count(db, User), await count(db, LoginSession)) == (0, 0)


async def test_unverified_google_email_is_denied(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    response = await finish_login(client, google, email_verified=False)

    assert response.headers["location"] == f"{APP_URL}/?login=denied"
    assert await count(db, LoginSession) == 0


# --- Identidad por emisor y sujeto ---


async def test_known_identity_with_new_email_is_the_same_user(
    client: httpx2.AsyncClient,
    google: FakeGoogle,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ccap.auth import settings

    monkeypatch.setattr(settings, "allowed_emails", f"{ALLOWED_EMAIL},nuevo@example.com")
    await finish_login(client, google)

    await finish_login(client, google, email="nuevo@example.com")

    identity = (await db.execute(select(UserIdentity))).scalar_one()
    assert identity.email == "nuevo@example.com"
    assert await count(db, User) == 1


async def test_second_identity_belongs_to_the_same_user(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    await finish_login(client, google)

    await finish_login(client, google, sub="google-sub-2")

    user_ids = set((await db.execute(select(UserIdentity.user_id))).scalars())
    assert len(user_ids) == 1
    assert await count(db, UserIdentity) == 2


# --- Sesión segura ---


async def test_session_cookie_is_httponly_secure_lax_root(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    response = await finish_login(client, google)

    cookie = response.headers["set-cookie"].lower()
    assert all(part in cookie for part in ("httponly", "secure", "samesite=lax", "path=/"))


async def test_new_login_replaces_previous_session(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    await finish_login(client, google)
    old_token = client.cookies[SESSION_COOKIE]

    await finish_login(client, google)

    new_token = client.cookies[SESSION_COOKIE]
    old = await me_with(client, old_token)
    assert new_token != old_token
    assert old.status_code == 401


async def test_expired_session_is_rejected(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    await finish_login(client, google)
    session = (await db.execute(select(LoginSession))).scalar_one()
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db.flush()

    response = await client.get("/api/auth/me")

    assert response.status_code == 401


async def test_invented_session_cookie_is_rejected(client: httpx2.AsyncClient) -> None:
    response = await me_with(client, "inventada")

    assert response.status_code == 401


# --- Consultar la sesión activa ---


async def test_me_returns_email_and_provider(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    await finish_login(client, google)

    response = await client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": ALLOWED_EMAIL, "provider": "google"}


async def test_me_without_session_is_401(client: httpx2.AsyncClient) -> None:
    response = await client.get("/api/auth/me")

    assert response.status_code == 401


# --- Cerrar sesión ---


async def test_logout_invalidates_session_and_clears_cookie(
    client: httpx2.AsyncClient, google: FakeGoogle
) -> None:
    await finish_login(client, google)
    token = client.cookies[SESSION_COOKIE]

    response = await client.post("/api/auth/logout")

    cookie_cleared = SESSION_COOKIE not in client.cookies
    after = await me_with(client, token)
    assert response.status_code == 204
    assert cookie_cleared
    assert after.status_code == 401


# --- Auditoría ---


async def test_login_logout_and_denial_are_audited_without_email(
    client: httpx2.AsyncClient, google: FakeGoogle, db: AsyncSession
) -> None:
    await finish_login(client, google)
    await client.post("/api/auth/logout")
    await finish_login(client, google, email="intrusa@example.com")

    rows = (await db.execute(select(AuditLog).order_by(AuditLog.id))).scalars().all()

    assert [(r.event, r.provider, r.reason) for r in rows] == [
        ("login_succeeded", "google", None),
        ("logout", None, None),
        ("login_denied", "google", "email_not_allowed"),
    ]
    assert rows[0].user_id is not None and rows[0].user_id == rows[1].user_id
    assert rows[2].user_id is None
