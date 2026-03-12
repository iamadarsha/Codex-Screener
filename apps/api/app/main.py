from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from data.nse_fallback import router as nse_fallback_router
from data.upstox_auth import router as upstox_auth_router
from data.upstox_instruments import router as upstox_instruments_router
from data.upstox_streamer import get_streamer_manager, router as upstox_streamer_router
from tasks.daily_setup import get_daily_setup_service, router as daily_setup_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    daily_setup = get_daily_setup_service()
    await daily_setup.start()
    yield
    await daily_setup.stop()
    streamer = get_streamer_manager()
    await streamer.stop()


settings = get_settings()

app = FastAPI(
    title="BreakoutScan API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.next_public_api_url.replace("8001", "3000").replace("8000", "3000"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "BreakoutScan API"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(upstox_auth_router)
app.include_router(upstox_instruments_router)
app.include_router(upstox_streamer_router)
app.include_router(nse_fallback_router)
app.include_router(daily_setup_router)
