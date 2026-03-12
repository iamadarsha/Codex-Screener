from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ws import ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    # Initialize Redis connection pool on startup
    try:
        from app.services.redis_cache import get_redis

        redis = await get_redis()
        logger.info("Redis connected: %s", await redis.ping())
    except Exception:
        logger.warning("Redis not available at startup – features relying on it will degrade gracefully")
    yield


settings = get_settings()

app = FastAPI(
    title="BreakoutScan API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        settings.next_public_api_url.replace("8000", "3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all HTTP API routes
app.include_router(api_router)

# Include WebSocket routes
app.include_router(ws_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "BreakoutScan API"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
