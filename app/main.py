import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import debug, health, manage, redirect, shorten
from app.sync_worker import flush_clicks_to_db, start_click_sync_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    sync_task = asyncio.create_task(start_click_sync_worker())
    try:
        yield
    finally:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
        await flush_clicks_to_db()



app = FastAPI(
    title="URL Shortener API",
    description=(
        "High-performance URL shortener with custom aliases, configurable expiration, "
        "and a Postgres + Redis dual-database architecture."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(debug.router)
app.include_router(shorten.router)
app.include_router(manage.router)
app.include_router(redirect.router)
