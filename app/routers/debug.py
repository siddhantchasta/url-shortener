from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_api_key
from app.config import settings
from app.database import get_db
from app.models import URL
from app.redis_client import get_redis

router = APIRouter(prefix="/debug", tags=["debug"], dependencies=[Depends(require_api_key)])


def _guard_debug_mode() -> None:
    if not settings.debug_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/stats")
async def debug_stats(db: AsyncSession = Depends(get_db), redis_client=Depends(get_redis)):
    _guard_debug_mode()

    total_urls = await db.scalar(select(func.count()).select_from(URL))
    total_clicks = await db.scalar(select(func.coalesce(func.sum(URL.click_count), 0)))
    redis_keys = await redis_client.dbsize()

    return {
        "total_urls": total_urls,
        "total_clicks": total_clicks,
        "redis_cached_keys": redis_keys,
    }


@router.get("/cache/{short_code}")
async def debug_cache_entry(short_code: str, redis_client=Depends(get_redis)):
    _guard_debug_mode()

    value = await redis_client.get(f"url:{short_code}")
    ttl = await redis_client.ttl(f"url:{short_code}")

    return {
        "short_code": short_code,
        "cached": value is not None,
        "cached_value": value,
        "ttl_seconds": ttl if ttl and ttl > 0 else None,
    }
