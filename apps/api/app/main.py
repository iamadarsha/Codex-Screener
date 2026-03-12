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
    import asyncio

    from app.services.nse_poller import nse_poller_loop

    configure_logging()
    logger.info("BreakoutScan API starting up...")
    poller_task = None
    # Initialize Redis connection pool on startup (with timeout so healthcheck passes)
    try:
        from app.services.redis_cache import get_redis

        redis = await asyncio.wait_for(get_redis(), timeout=5.0)
        pong = await asyncio.wait_for(redis.ping(), timeout=5.0)
        logger.info("Redis connected: %s", pong)
        # Start NSE background poller
        poller_task = asyncio.create_task(nse_poller_loop())
        logger.info("NSE poller task started")
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out – starting without Redis")
    except Exception as exc:
        logger.warning("Redis not available at startup (%s) – features relying on it will degrade gracefully", exc)
    logger.info("BreakoutScan API ready")
    yield
    # Cleanup
    if poller_task is not None:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass
        logger.info("NSE poller task stopped")


settings = get_settings()

app = FastAPI(
    title="BreakoutScan API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
