from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión de base de datos por petición. Quien la usa decide cuándo hacer commit."""
    async with AsyncSession(request.app.state.engine, expire_on_commit=False) as session:
        yield session
