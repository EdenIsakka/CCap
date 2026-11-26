import uuid

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ccap.audit import AuditEvent, AuditReason, record_event
from ccap.models import AuditLog


async def test_records_event_with_provider_user_and_time(db: AsyncSession) -> None:
    user_id = uuid.uuid4()

    await record_event(db, AuditEvent.LOGIN_SUCCEEDED, provider="google", user_id=user_id)

    entry = (await db.execute(select(AuditLog))).scalar_one()
    assert (entry.event, entry.provider, entry.user_id) == ("login_succeeded", "google", user_id)
    assert entry.created_at.tzinfo is not None


async def test_records_denied_login_with_reason_and_no_user(db: AsyncSession) -> None:
    await record_event(
        db, AuditEvent.LOGIN_DENIED, provider="google", reason=AuditReason.EMAIL_NOT_ALLOWED
    )

    entry = (await db.execute(select(AuditLog))).scalar_one()
    assert (entry.event, entry.reason, entry.user_id) == ("login_denied", "email_not_allowed", None)


async def test_audit_entry_cannot_be_updated(db: AsyncSession) -> None:
    await record_event(db, AuditEvent.LOGOUT, provider="google")

    with pytest.raises(DBAPIError, match="solo inserción"):
        async with db.begin_nested():
            await db.execute(update(AuditLog).values(event="login_succeeded"))

    entry = (await db.execute(select(AuditLog))).scalar_one()
    await db.refresh(entry)
    assert entry.event == "logout"


async def test_audit_entry_cannot_be_deleted(db: AsyncSession) -> None:
    await record_event(db, AuditEvent.LOGOUT, provider="google")

    with pytest.raises(DBAPIError, match="solo inserción"):
        async with db.begin_nested():
            await db.execute(delete(AuditLog))

    count = len((await db.execute(select(AuditLog))).scalars().all())
    assert count == 1
