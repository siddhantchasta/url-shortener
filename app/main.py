from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import redirect, shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="URL Shortener API",
    description="High-performance URL shortener with custom aliases and configurable expiration.",
    version="0.2.0",
    lifespan=lifespan,
)

# redirect.router owns a catch-all "/{short_code}" route — it must stay last
# or it will swallow requests meant for more specific routes added later.
app.include_router(shorten.router)
app.include_router(redirect.router)
