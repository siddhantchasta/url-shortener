from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app import crud
from app.database import AsyncSessionLocal, get_db
from app.redis_client import get_redis

router = APIRouter(tags=["redirect"])


async def _increment_click_count_task(short_code: str) -> None:
    """Opens its own DB session — the request-scoped one may already be closed
    by the time this background task actually runs."""
    async with AsyncSessionLocal() as session:
        await crud.increment_click_count(session, short_code)


@router.get("/{short_code}")
async def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    redis_client=Depends(get_redis),
):
    cached_url = await redis_client.get(f"url:{short_code}")
    if cached_url is not None:
        background_tasks.add_task(_increment_click_count_task, short_code)
        return RedirectResponse(url=cached_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    url = await crud.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

    if url.expires_at is not None and url.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Short URL has expired")

    ttl = None
    if url.expires_at is not None:
        ttl = max(int((url.expires_at - datetime.now(timezone.utc)).total_seconds()), 1)
    await redis_client.set(f"url:{short_code}", url.original_url, ex=ttl)

    background_tasks.add_task(_increment_click_count_task, short_code)
    return RedirectResponse(url=url.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
