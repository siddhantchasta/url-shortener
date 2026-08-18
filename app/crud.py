from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import URL


async def create_url(
    db: AsyncSession,
    short_code: str,
    original_url: str,
    expires_in_hours: int,
) -> URL:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    url = URL(short_code=short_code, original_url=original_url, expires_at=expires_at)
    db.add(url)
    await db.commit()
    await db.refresh(url)
    return url


async def get_url_by_code(db: AsyncSession, short_code: str) -> URL | None:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    return result.scalar_one_or_none()


async def increment_click_count(db: AsyncSession, short_code: str) -> None:
    await db.execute(
        update(URL).where(URL.short_code == short_code).values(click_count=URL.click_count + 1)
    )
    await db.commit()
