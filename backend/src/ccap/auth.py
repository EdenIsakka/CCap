"""Login con OIDC y sesión del lado del servidor (RF-01, ADR-0008, STRIDE S-01 y S-02)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from joserfc.errors import JoseError
from pydantic import BaseModel
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ccap.audit import AuditEvent, AuditReason, record_event
from ccap.db import get_session
from ccap.models import LoginSession, User, UserIdentity
from ccap.settings import get_settings

SESSION_COOKIE = "ccap_session"
SESSION_TTL = timedelta(hours=12)

LoginProvider = Literal["google"]

settings = get_settings()

oauth = OAuth()
oauth.register(
    "google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    # Solo identidad: los permisos de correo llegan con RF-02 (RS-01).
    client_kwargs={"scope": "openid email", "code_challenge_method": "S256"},
)

router = APIRouter(prefix="/auth")

DbSession = Annotated[AsyncSession, Depends(get_session)]


def _hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


async def current_session(request: Request, db: DbSession) -> LoginSession:
    """Sesión válida de la cookie, o 401. Todo endpoint que no sea público la exige (E-02)."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        session = await db.get(LoginSession, _hash(token))
        if session is not None and session.expires_at > datetime.now(UTC):
            return session
    raise HTTPException(status.HTTP_401_UNAUTHORIZED)


CurrentSession = Annotated[LoginSession, Depends(current_session)]


@router.get("/{provider}/login")
async def login(provider: LoginProvider, request: Request) -> Response:
    redirect_uri = f"{settings.app_url}/api/auth/{provider}/callback"
    response: Response = await oauth.create_client(provider).authorize_redirect(
        request, redirect_uri
    )
    return response


@router.get("/{provider}/callback")
async def callback(provider: LoginProvider, request: Request, db: DbSession) -> Response:
    # authlib valida state (atado a este navegador), PKCE, y firma, iss, aud, exp y nonce
    # del ID token (STRIDE S-01).
    try:
        token: dict[str, Any] = await oauth.create_client(provider).authorize_access_token(request)
    except (OAuthError, JoseError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inicio de sesión inválido") from exc
    claims = token.get("userinfo")
    if claims is None or not isinstance(claims.get("email"), str):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inicio de sesión inválido")
    email: str = claims["email"]

    if claims.get("email_verified") is not True:
        return await _deny(db, provider, AuditReason.EMAIL_NOT_VERIFIED)
    if not settings.is_email_allowed(email):
        return await _deny(db, provider, AuditReason.EMAIL_NOT_ALLOWED)

    identity = await _identity_for(db, provider, claims["iss"], claims["sub"], email)
    session_token = await _start_session(db, identity, request.cookies.get(SESSION_COOKIE))
    await record_event(db, AuditEvent.LOGIN_SUCCEEDED, provider=provider, user_id=identity.user_id)
    await db.commit()

    response = RedirectResponse(f"{settings.app_url}/", status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return response


async def _deny(db: AsyncSession, provider: LoginProvider, reason: AuditReason) -> Response:
    # Sin el correo: la auditoría no guarda datos de cuentas ajenas.
    await record_event(db, AuditEvent.LOGIN_DENIED, provider=provider, reason=reason)
    await db.commit()
    return RedirectResponse(f"{settings.app_url}/?login=denied", status.HTTP_303_SEE_OTHER)


async def _identity_for(
    db: AsyncSession, provider: LoginProvider, issuer: str, subject: str, email: str
) -> UserIdentity:
    """Busca la identidad por emisor + sujeto, o la crea para el único usuario (ADR-0008).

    Estas consultas no filtran por user_id porque aún no hay sesión: es el login.
    """
    identity = await db.scalar(
        select(UserIdentity).where(UserIdentity.issuer == issuer, UserIdentity.subject == subject)
    )
    if identity is not None:
        identity.email = email
        return identity

    user_id = await db.scalar(select(User.id).limit(1))
    if user_id is None:
        user = User()
        db.add(user)
        await db.flush()
        user_id = user.id
    identity = UserIdentity(
        user_id=user_id, provider=provider, issuer=issuer, subject=subject, email=email
    )
    db.add(identity)
    await db.flush()
    return identity


async def _start_session(
    db: AsyncSession, identity: UserIdentity, previous_token: str | None
) -> str:
    """Crea una sesión nueva y borra la anterior de este navegador y las vencidas."""
    now = datetime.now(UTC)
    stale = [LoginSession.expires_at <= now]
    if previous_token:
        stale.append(LoginSession.token_hash == _hash(previous_token))
    await db.execute(delete(LoginSession).where(or_(*stale)))

    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=_hash(token),
            user_id=identity.user_id,
            identity_id=identity.id,
            expires_at=now + SESSION_TTL,
        )
    )
    await db.flush()
    return token


class Me(BaseModel):
    email: str
    provider: str


@router.get("/me")
async def me(session: CurrentSession, db: DbSession) -> Me:
    identity = await db.get_one(UserIdentity, session.identity_id)
    return Me(email=identity.email, provider=identity.provider)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(session: CurrentSession, db: DbSession) -> Response:
    await db.delete(session)
    await record_event(db, AuditEvent.LOGOUT, user_id=session.user_id)
    await db.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return response
