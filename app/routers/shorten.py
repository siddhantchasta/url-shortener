from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, utils
from app.auth import require_api_key
from app.config import settings
from app.database import get_db
from app.rate_limiter import rate_limiter
from app.redis_client import get_redis
from app.schemas import URLCreateRequest, URLResponse

router = APIRouter(prefix="/api/v1/urls", tags=["urls"])

MAX_CODE_GENERATION_ATTEMPTS = 5


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter), Depends(require_api_key)],
)
async def shorten_url(
    payload: URLCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    if payload.custom_alias:
        short_code = payload.custom_alias
        existing = await crud.get_url_by_code(db, short_code)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Short code already in use")
    else:
        short_code = None
        for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
            candidate = utils.generate_short_code(settings.short_code_length)
            existing = await crud.get_url_by_code(db, candidate)
            if existing is None:
                short_code = candidate
                break
        if short_code is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not generate a unique short code, try again",
            )

    expires_in_hours = payload.expires_in_hours or settings.default_expiry_hours

    url = await crud.create_url(
        db,
        short_code=short_code,
        original_url=str(payload.url),
        expires_in_hours=expires_in_hours,
    )

    ttl_seconds = expires_in_hours * 3600
    await redis_client.set(f"url:{short_code}", url.original_url, ex=ttl_seconds)

    return URLResponse(
        short_code=url.short_code,
        short_url=utils.build_short_url(settings.domain, url.short_code),
        original_url=url.original_url,
        created_at=url.created_at,
        expires_at=url.expires_at,
        click_count=url.click_count,
    )
