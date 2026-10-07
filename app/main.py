from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import models

from app.auth.router import router as auth_router
from app.campaigns.router import router as campaign_router
from app.campaign_memberships.router import router as campaign_memberships_router
from app.qr_sessions.router import router as qr_sessions_router

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    campaign_router,
    prefix="/api/v1",
)

app.include_router(
    campaign_memberships_router,
    prefix="/api/v1",
)

app.include_router(
    qr_sessions_router,
    prefix="/api/v1",
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.ico")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await db.execute(text("SELECT 1"))

    return {"database": "ok"}


@app.get("/health/redis")
async def redis_health_check(
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    await redis.ping()

    return {"redis": "ok"}