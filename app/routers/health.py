from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    services = {"postgres": "unknown", "redis": "unknown"}
    healthy = True

    try:
        await db.execute(text("SELECT 1"))
        services["postgres"] = "up"
    except Exception:
        services["postgres"] = "down"
        healthy = False

    try:
        await redis_client.ping()
        services["redis"] = "up"
    except Exception:
        services["redis"] = "down"
        healthy = False

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "healthy" if healthy else "unhealthy", "services": services}
