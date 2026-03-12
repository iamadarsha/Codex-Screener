"""Upstox instrument CSV sync and Redis-backed lookups."""

from __future__ import annotations

import csv
import gzip
import io
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.stock import Stock
from app.db.session import SessionLocal
from app.services.redis_cache import get_redis, hset_dict
from app.utils.redis_keys import (
    KEY_KEY_TO_SYMBOL,
    KEY_SYMBOL_TO_KEY,
    KEY_UNIVERSE_NIFTY50,
    KEY_UNIVERSE_NIFTY500,
    TTL_INSTRUMENT_MAP,
    TTL_UNIVERSE,
)
from app.utils.retry import async_retry

log = structlog.get_logger(__name__)

_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"


@async_retry(max_attempts=3, min_wait=2.0, max_wait=30.0)
async def download_instruments() -> bytes:
    """Download the gzipped NSE instrument CSV from Upstox.

    Returns the raw CSV bytes (decompressed).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(_INSTRUMENTS_URL)
        resp.raise_for_status()

    raw = gzip.decompress(resp.content)
    log.info("instruments_downloaded", size_bytes=len(raw))
    return raw


def parse_instruments(csv_data: bytes) -> tuple[dict[str, str], dict[str, str]]:
    """Parse the Upstox CSV and build bi-directional maps.

    Returns
    -------
    symbol_to_key:
        Mapping of trading symbol -> instrument_key.
    key_to_symbol:
        Mapping of instrument_key -> trading symbol.
    """
    symbol_to_key: dict[str, str] = {}
    key_to_symbol: dict[str, str] = {}

    reader = csv.DictReader(io.StringIO(csv_data.decode("utf-8")))
    for row in reader:
        instrument_key = row.get("instrument_key", "").strip()
        trading_symbol = row.get("trading_symbol", "").strip()
        instrument_type = row.get("instrument_type", "").strip()
        exchange = row.get("exchange", "").strip()

        # Only keep equity instruments from NSE
        if not instrument_key or not trading_symbol:
            continue
        if exchange != "NSE" or instrument_type not in ("EQ", "EQUITY"):
            continue

        symbol_to_key[trading_symbol] = instrument_key
        key_to_symbol[instrument_key] = trading_symbol

    log.info("instruments_parsed", count=len(symbol_to_key))
    return symbol_to_key, key_to_symbol


async def sync_to_redis(
    symbol_to_key: dict[str, str] | None = None,
    key_to_symbol: dict[str, str] | None = None,
) -> None:
    """Store instrument maps in Redis hashes with a 24-hour TTL.

    If maps are not provided, downloads and parses them first.
    """
    if symbol_to_key is None or key_to_symbol is None:
        csv_data = await download_instruments()
        symbol_to_key, key_to_symbol = parse_instruments(csv_data)

    await hset_dict(KEY_SYMBOL_TO_KEY, symbol_to_key, ttl=TTL_INSTRUMENT_MAP)
    await hset_dict(KEY_KEY_TO_SYMBOL, key_to_symbol, ttl=TTL_INSTRUMENT_MAP)
    log.info("instruments_synced_to_redis", symbols=len(symbol_to_key))


async def get_instrument_key(symbol: str) -> str | None:
    """Look up an instrument key by trading symbol from Redis."""
    r = await get_redis()
    return await r.hget(KEY_SYMBOL_TO_KEY, symbol)


async def get_symbol(instrument_key: str) -> str | None:
    """Reverse-look up a trading symbol from an instrument key in Redis."""
    r = await get_redis()
    return await r.hget(KEY_KEY_TO_SYMBOL, instrument_key)


async def refresh_universe_sets() -> None:
    """Populate ``universe:nifty50`` and ``universe:nifty500`` Redis sets.

    Cross-references the ``stocks`` table with Redis instrument maps to build
    the sets.
    """
    r = await get_redis()

    async with SessionLocal() as session:
        session: AsyncSession
        nifty50_rows: list[Any] = (
            (await session.execute(select(Stock.symbol).where(Stock.is_nifty50.is_(True))))
            .scalars()
            .all()
        )
        nifty500_rows: list[Any] = (
            (await session.execute(select(Stock.symbol).where(Stock.is_nifty500.is_(True))))
            .scalars()
            .all()
        )

    pipe = r.pipeline()

    # Nifty 50
    await pipe.delete(KEY_UNIVERSE_NIFTY50)
    if nifty50_rows:
        await pipe.sadd(KEY_UNIVERSE_NIFTY50, *nifty50_rows)
    await pipe.expire(KEY_UNIVERSE_NIFTY50, TTL_UNIVERSE)

    # Nifty 500
    await pipe.delete(KEY_UNIVERSE_NIFTY500)
    if nifty500_rows:
        await pipe.sadd(KEY_UNIVERSE_NIFTY500, *nifty500_rows)
    await pipe.expire(KEY_UNIVERSE_NIFTY500, TTL_UNIVERSE)

    await pipe.execute()
    log.info(
        "universe_sets_refreshed",
        nifty50=len(nifty50_rows),
        nifty500=len(nifty500_rows),
    )
