from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="URL Shortener API",
    description="High-performance URL shortener with custom aliases and configurable expiration.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(shorten.router)
