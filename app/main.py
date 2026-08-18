from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import debug, health, manage, redirect, shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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
