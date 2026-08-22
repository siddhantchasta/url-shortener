import asyncio
import logging
import redis.asyncio as redis

from app import crud
from app.database import AsyncSessionLocal
from app.redis_client import redis_pool

logger = logging.getLogger("app.sync_worker")


async def flush_clicks_to_db() -> None:
    """Scans all pending in-memory click count keys from Redis and updates
    PostgreSQL in batches, clearing the Redis counters atomically."""
    client = redis.Redis(connection_pool=redis_pool)
    try:
        keys = []
        async for key in client.scan_iter("clicks:*"):
            keys.append(key)

        if not keys:
            return

        async with AsyncSessionLocal() as db:
            for key in keys:
                count_str = await client.getdel(key)
                if count_str is not None:
                    count = int(count_str)
                    if count > 0:
                        short_code = key.split(":", 1)[1]
                        await crud.increment_click_count_by_amount(db, short_code, count)
    except Exception as e:
        logger.error(f"Error flushing clicks to database: {e}")
    finally:
        await client.aclose()


async def start_click_sync_worker(interval_seconds: int = 10) -> None:
    """Background loop that periodically executes the flush task."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await flush_clicks_to_db()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Sync worker loop error: {e}")
