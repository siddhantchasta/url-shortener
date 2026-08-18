from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as redis

from app.config import settings
from app.redis_client import get_redis


async def rate_limiter(request: Request, redis_client: redis.Redis = Depends(get_redis)) -> None:
    """Fixed-window limiter keyed by client IP. Known trade-off: allows a burst
    right at the window boundary — a sliding-window/token-bucket limiter avoids
    that, worth naming if asked how you'd improve this."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    current = await redis_client.get(key)

    if current is None:
        await redis_client.set(key, settings.api_quota - 1, ex=settings.rate_limit_window_seconds)
        return

    remaining = int(current)
    if remaining <= 0:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "Rate limit exceeded", "retry_after_seconds": ttl},
        )

    await redis_client.decr(key)
