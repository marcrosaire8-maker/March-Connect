import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.rate_limit import limiter
from app.db.config import settings
from app.db.bootstrap import (
    ensure_admin_user,
    ensure_notification_abonnes,
    ensure_scraper_sources,
    ensure_sectors,
)
from app.services.email_delivery import log_email_config_status
from app.db.connection import close_client, get_database
from app.db.indexes import ensure_indexes
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    await db.command("ping")
    await ensure_indexes(db)
    await ensure_sectors(db)
    await ensure_admin_user(db)
    await ensure_notification_abonnes(db)
    await ensure_scraper_sources(db)
    log_email_config_status()
    start_scheduler()
    yield
    stop_scheduler()
    await close_client()


app = FastAPI(
    title="MarchéConnect API",
    description="Plateforme de collecte et classification des appels d'offres",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

def _cors_origins() -> list[str]:
    origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    if settings.frontend_url:
        origins.add(settings.frontend_url.rstrip("/"))
    for origin in os.getenv("CORS_ORIGINS", "").split(","):
        value = origin.strip()
        if value:
            origins.add(value.rstrip("/"))
    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    db = get_database()
    await db.command("ping")
    return {"status": "ok", "database": "connected"}
