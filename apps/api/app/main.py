from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

print("BreakoutScan: loading main module...", file=sys.stderr, flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ws import ws_router

logger = logging.getLogger(__name__)
print("BreakoutScan: all imports OK", file=sys.stderr, flush=True)


_poller_running = False
_universe_size = 0


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _poller_running, _universe_size
    import asyncio

    from app.services.nse_poller import nse_poller_loop, populate_universe_fallback

    configure_logging()
    logger.info("BreakoutScan API starting up...")

    # Log configured API keys (masked) for debugging
    settings = get_settings()
    logger.info(
        "Config: GEMINI_API_KEY=%s, INDIAN_API_KEY=%s, REDIS_URL=%s",
        "***set***" if settings.gemini_api_key else "MISSING",
        "***set***" if settings.indian_api_key else "MISSING",
        settings.redis_url[:30] + "..." if settings.redis_url else "MISSING",
    )

    poller_task = None
    try:
        from app.services.redis_cache import get_redis

        redis = await asyncio.wait_for(get_redis(), timeout=10.0)
        pong = await asyncio.wait_for(redis.ping(), timeout=5.0)
        logger.info("Redis connected: %s", pong)

        # Immediately populate universe so screener works from first request
        try:
            symbols = await populate_universe_fallback()
            _universe_size = len(symbols)
            logger.info("Universe pre-populated with %d symbols", _universe_size)
        except Exception as e:
            logger.warning("Failed to pre-populate universe: %s", e)

        # Start NSE background poller
        poller_task = asyncio.create_task(nse_poller_loop())
        _poller_running = True
        logger.info("NSE poller task started")
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out – starting without Redis")
    except Exception as exc:
        logger.warning("Redis not available at startup (%s) – features relying on it will degrade gracefully", exc)
    logger.info("BreakoutScan API ready")
    yield
    # Cleanup
    _poller_running = False
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

_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://breakoutscan.up.railway.app",
    "https://breakoutscan-web-production.up.railway.app",
    "https://breakoutscan.in",
    "https://www.breakoutscan.in",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include all HTTP API routes
app.include_router(api_router)

# Include WebSocket routes
app.include_router(ws_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "BreakoutScan API"}


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "poller": "running" if _poller_running else "stopped",
        "universe_size": _universe_size,
    }
