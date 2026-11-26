import uuid
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from ccap.models import AuditLog, Provider


class AuditEvent(StrEnum):
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_DENIED = "login_denied"
    LOGOUT = "logout"


class AuditReason(StrEnum):
    EMAIL_NOT_ALLOWED = "email_not_allowed"
    EMAIL_NOT_VERIFIED = "email_not_verified"


async def record_event(
    session: AsyncSession,
    event: AuditEvent,
    *,
    provider: Provider | None = None,
    user_id: uuid.UUID | None = None,
    reason: AuditReason | None = None,
) -> None:
    """Registra un evento de seguridad (RS-11).

    Solo acepta valores fijos: sin texto libre no se cuelan correos ni tokens.
    No hace commit: el evento entra en la transacción de quien llama.
    """
    session.add(AuditLog(event=event, provider=provider, user_id=user_id, reason=reason))
    await session.flush()
