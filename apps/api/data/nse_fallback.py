from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import cast

from curl_cffi import requests
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from data.upstox_streamer import get_streamer_manager

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["nse-fallback"])

NSE_HOME_URL = "https://www.nseindia.com"
NSE_ALL_INDICES_URL = "https://www.nseindia.com/api/allIndices"
NSE_QUOTE_URL = "https://www.nseindia.com/api/quote-equity"
NSE_INDICES_CACHE_KEY = "nse:indices"

_redis_client: redis.Redis[str] | None = None


class NSEFallbackError(BreakoutScanError):
    """Raised when the NSE fallback APIs fail."""


def get_redis_client() -> redis.Redis[str]:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def create_session() -> requests.Session:
    session = requests.Session(impersonate="chrome")
    session.headers.update(
        {
            "accept": "application/json,text/plain,*/*",
            "referer": NSE_HOME_URL,
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            ),
        }
    )
    return session


def bootstrap_session_sync(session: requests.Session) -> None:
    try:
        response = session.get(NSE_HOME_URL, timeout=30)
        response.raise_for_status()
    except Exception as error:
        raise NSEFallbackError("Unable to bootstrap the NSE cookie session.") from error


def fetch_json_sync(url: str, params: dict[str, str] | None = None) -> dict[str, object]:
    session = create_session()
    bootstrap_session_sync(session)
    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return cast(dict[str, object], response.json())
    except Exception as error:
        raise NSEFallbackError(f"Unable to fetch NSE data from {url}.") from error


async def fetch_json(url: str, params: dict[str, str] | None = None) -> dict[str, object]:
    try:
        return await asyncio.to_thread(fetch_json_sync, url, params)
    except NSEFallbackError:
        raise
    except Exception as error:
        raise NSEFallbackError(f"Unexpected error while fetching NSE data from {url}.") from error


async def is_fallback_active() -> bool:
    manager = get_streamer_manager()
    if manager.last_tick_at is None:
        return True

    silence_window = timedelta(seconds=settings.nse_fallback_silence_seconds)
    return datetime.now(tz=UTC) - manager.last_tick_at > silence_window


async def fetch_indices() -> dict[str, object]:
    payload = await fetch_json(NSE_ALL_INDICES_URL)
    rows = cast(list[dict[str, object]], payload.get("data", []))
    normalized = [
        {
            "index": row.get("index"),
            "last": row.get("last"),
            "variation": row.get("variation"),
            "percent_change": row.get("percentChange"),
            "advances": row.get("advances"),
            "declines": row.get("declines"),
        }
        for row in rows
    ]

    redis_client = get_redis_client()
    try:
        await redis_client.set(
            NSE_INDICES_CACHE_KEY,
            json.dumps(normalized),
            ex=settings.redis_short_ttl_seconds,
        )
    except redis.RedisError as error:
        raise NSEFallbackError("Unable to cache NSE index data in Redis.") from error

    return {
        "source": "nse_fallback",
        "fallback_active": await is_fallback_active(),
        "count": len(normalized),
        "indices": normalized,
    }


async def fetch_quote(symbol: str) -> dict[str, object]:
    payload = await fetch_json(NSE_QUOTE_URL, params={"symbol": symbol.upper()})
    info = cast(dict[str, object], payload.get("info", {}))
    price_info = cast(dict[str, object], payload.get("priceInfo", {}))
    security_info = cast(dict[str, object], payload.get("securityInfo", {}))
    intraday = cast(dict[str, object], price_info.get("intraDayHighLow", {}))
    week_range = cast(dict[str, object], security_info.get("weekHighLow", {}))

    normalized = {
        "symbol": symbol.upper(),
        "company_name": info.get("companyName"),
        "industry": info.get("industry"),
        "last_price": price_info.get("lastPrice"),
        "previous_close": price_info.get("previousClose"),
        "change": price_info.get("change"),
        "percent_change": price_info.get("pChange"),
        "day_high": intraday.get("max"),
        "day_low": intraday.get("min"),
        "week_high_52": week_range.get("max"),
        "week_low_52": week_range.get("min"),
    }

    redis_client = get_redis_client()
    try:
        await redis_client.set(
            f"nse:quote:{symbol.upper()}",
            json.dumps(normalized),
            ex=settings.redis_short_ttl_seconds,
        )
    except redis.RedisError as error:
        raise NSEFallbackError(f"Unable to cache the NSE quote for {symbol.upper()}.") from error

    return normalized


@router.get("/api/indices")
async def api_indices() -> dict[str, object]:
    try:
        return await fetch_indices()
    except NSEFallbackError as error:
        logger.exception("nse indices fallback failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.get("/api/data/nse/status")
async def nse_status() -> dict[str, object]:
    try:
        return {
            "fallback_active": await is_fallback_active(),
            "silence_threshold_seconds": settings.nse_fallback_silence_seconds,
        }
    except NSEFallbackError as error:
        logger.exception("nse fallback status failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/api/data/nse/quote/{symbol}")
async def nse_quote(symbol: str) -> dict[str, object]:
    try:
        return await fetch_quote(symbol)
    except NSEFallbackError as error:
        logger.exception("nse quote fallback failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
