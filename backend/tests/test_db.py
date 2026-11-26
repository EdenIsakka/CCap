from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_connects_to_postgres(db: AsyncSession) -> None:
    result = await db.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
