from __future__ import annotations

import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager

print("BreakoutScan: loading main module...", file=sys.stderr, flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.ws import ws_router

logger = logging.getLogger(__name__)
print("BreakoutScan: all imports OK", file=sys.stderr, flush=True)


_poller_running = False
_universe_size = 0
_startup_time: float = 0.0


async def _poller_watchdog() -> None:
    """Run nse_poller_loop forever, restarting it if it ever raises.

    Uses exponential back-off (5 s → 10 s → 20 s … capped at 5 min) so a
    persistent crash doesn't spin-loop and exhaust CPU/memory.
    """
    global _poller_running

    from app.services.nse_poller import nse_poller_loop

    delay = 5
    while True:
        _poller_running = True
        try:
            logger.info("NSE poller (re)starting…")
            await nse_poller_loop()
        except asyncio.CancelledError:
            _poller_running = False
            raise
        except Exception as exc:
            _poller_running = False
            logger.error(
                "NSE poller crashed: %s — restarting in %ds", exc, delay
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, 300)  # cap at 5 minutes
        else:
            # nse_poller_loop returned normally (shouldn't happen); restart after 5 s
            _poller_running = False
            logger.warning("NSE poller exited unexpectedly — restarting in 5s")
            await asyncio.sleep(5)
            delay = 5  # reset backoff


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _poller_running, _universe_size, _startup_time
    _startup_time = time.monotonic()

    from app.services.nse_poller import populate_universe_fallback

    configure_logging()
    logger.info("BreakoutScan API starting up...")

    settings = get_settings()
    logger.info(
        "Config: GEMINI_API_KEY=%s, INDIAN_API_KEY=%s, REDIS_URL=%s",
        "***set***" if settings.gemini_api_key else "MISSING",
        "***set***" if settings.indian_api_key else "MISSING",
        settings.redis_url[:30] + "..." if settings.redis_url else "MISSING",
    )

    watchdog_task = None
    try:
        from app.services.redis_cache import get_redis

        redis = await asyncio.wait_for(get_redis(), timeout=10.0)
        pong = await asyncio.wait_for(redis.ping(), timeout=5.0)
        logger.info("Redis connected: %s", pong)

        # Pre-populate universe so the screener works from the very first request
        try:
            symbols = await populate_universe_fallback()
            _universe_size = len(symbols)
            logger.info("Universe pre-populated with %d symbols", _universe_size)
        except Exception as e:
            logger.warning("Failed to pre-populate universe: %s", e)
            symbols = []

        # Fire indicator compute immediately — don't wait for first NSE poll cycle.
        # This ensures Redis has RSI/EMA/SMA data before the first user scan request.
        if symbols:
            try:
                from app.services.nse_poller import _run_bulk_compute
                asyncio.create_task(
                    _run_bulk_compute(symbols), name="bulk_compute_startup"
                )
                logger.info("Startup bulk indicator compute fired for %d symbols", len(symbols))
            except Exception as e:
                logger.warning("Failed to fire startup bulk compute: %s", e)

        # Start self-healing watchdog (replaces the bare create_task)
        watchdog_task = asyncio.create_task(_poller_watchdog(), name="poller_watchdog")
        logger.info("NSE poller watchdog started")
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out – starting without Redis")
    except Exception as exc:
        logger.warning(
            "Redis not available at startup (%s) – features relying on it will degrade gracefully",
            exc,
        )

    logger.info("BreakoutScan API ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    _poller_running = False
    if watchdog_task is not None:
        watchdog_task.cancel()
        try:
            await watchdog_task
        except asyncio.CancelledError:
            pass
        logger.info("NSE poller watchdog stopped")


settings = get_settings()

app = FastAPI(
    title="BreakoutScan API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://breakoutscan.up.railway.app",
    "https://breakoutscan-web-production.up.railway.app",
    "https://screenercodex.netlify.app",
    "https://breakoutscan.in",
    "https://www.breakoutscan.in",
]
_extra = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
_allowed_origins = list(dict.fromkeys(_DEFAULT_ORIGINS + _extra))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "BreakoutScan API"}


@app.get("/ping", tags=["system"])
async def ping() -> dict[str, str]:
    """Lightweight liveness probe used by Railway / load balancers."""
    return {"pong": "ok"}


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Deep health check — reports Redis liveness, poller state, uptime."""
    from app.services.redis_cache import redis_ping

    redis_ok = await redis_ping()
    uptime_s = int(time.monotonic() - _startup_time) if _startup_time else 0

    overall = "ok" if redis_ok and _poller_running else "degraded"

    return {
        "status": overall,
        "redis": "ok" if redis_ok else "unavailable",
        "poller": "running" if _poller_running else "stopped",
        "universe_size": _universe_size,
        "uptime_seconds": uptime_s,
    }
