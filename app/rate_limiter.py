from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as redis

from app.config import settings
from app.redis_client import get_redis


def get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting proxy headers from Render/Nginx/Cloudflare."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host
    return "unknown"


async def rate_limiter(request: Request, redis_client: redis.Redis = Depends(get_redis)) -> None:
    """Fixed-window limiter keyed by client IP using atomic Redis INCR."""
    client_ip = get_client_ip(request)
    key = f"rate_limit:{client_ip}"

    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.rate_limit_window_seconds)

    if count > settings.api_quota:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "Rate limit exceeded", "retry_after_seconds": max(ttl, 1)},
        )

