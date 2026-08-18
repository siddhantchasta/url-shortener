from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import manage, redirect, shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="URL Shortener API",
    description="High-performance URL shortener with custom aliases and configurable expiration.",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(shorten.router)
app.include_router(manage.router)
app.include_router(redirect.router)
