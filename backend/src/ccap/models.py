import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, ForeignKey, LargeBinary, UniqueConstraint, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {datetime: DateTime(timezone=True)}


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserIdentity(Base):
    """Cuenta de login (Google o Microsoft), identificada por emisor + sujeto, no por correo."""

    __tablename__ = "user_identities"
    __table_args__ = (UniqueConstraint("issuer", "subject"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    issuer: Mapped[str]
    subject: Mapped[str]
    email: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class LoginSession(Base):
    """Sesión del lado del servidor. Solo se guarda el hash del token de la cookie."""

    __tablename__ = "sessions"

    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]


class AuditLog(Base):
    """Solo inserción: un trigger de la base rechaza UPDATE, DELETE y TRUNCATE."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    event: Mapped[str]
    provider: Mapped[str | None]
    # Sin llave foránea: borrar el usuario (RF-09) no debe tocar la auditoría.
    user_id: Mapped[uuid.UUID | None]
    reason: Mapped[str | None]
