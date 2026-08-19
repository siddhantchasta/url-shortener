from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, utils
from app.auth import require_api_key
from app.config import settings
from app.database import get_db
from app.redis_client import get_redis
from app.schemas import URLResponse, URLUpdateRequest

router = APIRouter(prefix="/api/v1/urls", tags=["urls"])


def _to_response(url) -> URLResponse:
    return URLResponse(
        short_code=url.short_code,
        short_url=utils.build_short_url(settings.domain, url.short_code),
        original_url=url.original_url,
        created_at=url.created_at,
        expires_at=url.expires_at,
        click_count=url.click_count,
    )


@router.get("/{short_code}", response_model=URLResponse)
async def get_url_info(short_code: str, db: AsyncSession = Depends(get_db)):
    url = await crud.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
    return _to_response(url)


@router.put("/{short_code}", response_model=URLResponse, dependencies=[Depends(require_api_key)])
async def edit_url(
    short_code: str,
    payload: URLUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    url = await crud.update_url(
        db,
        short_code,
        original_url=str(payload.url) if payload.url else None,
        expires_in_hours=payload.expires_in_hours,
    )
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

    if payload.url is not None:
        ttl = 1
        if url.expires_at is not None:
            ttl = max(int((url.expires_at - datetime.now(timezone.utc)).total_seconds()), 1)
        await redis_client.set(f"url:{short_code}", url.original_url, ex=ttl)

    return _to_response(url)


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)])
async def remove_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    deleted = await crud.delete_url(db, short_code)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
    await redis_client.delete(f"url:{short_code}")
