from __future__ import annotations

import asyncio
import csv
import gzip
import io
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from curl_cffi import requests
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import update

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from app.db.models.stock import Stock
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/data/instruments", tags=["upstox-instruments"])

NSE_INSTRUMENT_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
BSE_INSTRUMENT_URL = "https://assets.upstox.com/market-quote/instruments/exchange/BSE.csv.gz"
NSE_HOME_URL = "https://www.nseindia.com"
NSE_INDEX_URL = "https://www.nseindia.com/api/equity-stockIndices"

SYMBOL_TO_KEY_HASH = "instrument:symbol_to_key"
KEY_TO_SYMBOL_HASH = "instrument:key_to_symbol"
SYMBOL_META_HASH = "instrument:symbol_meta"
UNIVERSE_NIFTY50_KEY = "universe:nifty50"
UNIVERSE_NIFTY500_KEY = "universe:nifty500"
INSTRUMENT_SYNC_META_KEY = "instrument:sync:meta"

_redis_client: redis.Redis[str] | None = None


class InstrumentSyncError(BreakoutScanError):
    """Raised when the Upstox instrument sync fails."""


@dataclass(slots=True)
class InstrumentRecord:
    symbol: str
    instrument_key: str
    exchange: str
    instrument_type: str
    company_name: str | None
    last_price: Decimal | None

    def to_meta_value(self) -> str:
        payload = {
            "symbol": self.symbol,
            "instrument_key": self.instrument_key,
            "exchange": self.exchange,
            "instrument_type": self.instrument_type,
            "company_name": self.company_name,
            "last_price": str(self.last_price) if self.last_price is not None else None,
        }
        return json.dumps(payload)


@dataclass(slots=True)
class InstrumentSyncSummary:
    synced_at: str
    symbol_count: int
    reverse_count: int
    nifty50_count: int
    nifty500_count: int
    preferred_exchange: str

    def to_redis_mapping(self) -> dict[str, str]:
        return {
            key: str(value)
            for key, value in asdict(self).items()
        }


def get_redis_client() -> redis.Redis[str]:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def decimal_or_none(value: str | None) -> Decimal | None:
    if value is None or value == "":
        return None

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def fetch_bytes_sync(url: str) -> bytes:
    try:
        response = requests.get(
            url,
            impersonate="chrome",
            timeout=60,
            headers={"accept": "text/csv,*/*"},
        )
        response.raise_for_status()
    except Exception as error:
        raise InstrumentSyncError(f"Unable to download instrument data from {url}.") from error

    return response.content


async def fetch_bytes(url: str) -> bytes:
    try:
        return await asyncio.to_thread(fetch_bytes_sync, url)
    except InstrumentSyncError:
        raise
    except Exception as error:
        raise InstrumentSyncError(f"Unexpected error downloading instrument data from {url}.") from error


def parse_instrument_csv(content: bytes) -> list[InstrumentRecord]:
    try:
        decoded = gzip.decompress(content).decode("utf-8")
    except OSError as error:
        raise InstrumentSyncError("The downloaded instrument file is not valid gzip content.") from error

    reader = csv.DictReader(io.StringIO(decoded))
    rows: list[InstrumentRecord] = []

    for row in reader:
        instrument_type = str(row.get("instrument_type", "")).upper()
        exchange = str(row.get("exchange", ""))
        symbol = str(row.get("tradingsymbol", "")).strip().upper()
        instrument_key = str(row.get("instrument_key", "")).strip()

        if symbol == "" or instrument_key == "":
            continue

        if instrument_type != "EQUITY":
            continue

        if exchange not in {"NSE_EQ", "BSE_EQ"}:
            continue

        rows.append(
            InstrumentRecord(
                symbol=symbol,
                instrument_key=instrument_key,
                exchange=exchange,
                instrument_type=instrument_type,
                company_name=row.get("name"),
                last_price=decimal_or_none(row.get("last_price")),
            )
        )

    return rows


def create_nse_session() -> requests.Session:
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


def bootstrap_nse_session_sync(session: requests.Session) -> None:
    try:
        response = session.get(NSE_HOME_URL, timeout=30)
        response.raise_for_status()
    except Exception as error:
        raise InstrumentSyncError("Unable to bootstrap the NSE session.") from error


def fetch_index_members_sync(index_name: str) -> list[str]:
    session = create_nse_session()
    bootstrap_nse_session_sync(session)

    try:
        response = session.get(
            NSE_INDEX_URL,
            params={"index": index_name},
            timeout=30,
        )
        response.raise_for_status()
        payload = cast(dict[str, object], response.json())
    except Exception as error:
        raise InstrumentSyncError(f"Unable to fetch NSE constituents for {index_name}.") from error

    raw_rows = cast(list[dict[str, object]], payload.get("data", []))
    symbols = [
        str(row["symbol"]).upper()
        for row in raw_rows
        if row.get("symbol") not in {None, index_name}
    ]
    return sorted(set(symbols))


async def fetch_index_members(index_name: str) -> list[str]:
    try:
        return await asyncio.to_thread(fetch_index_members_sync, index_name)
    except InstrumentSyncError:
        raise
    except Exception as error:
        raise InstrumentSyncError(
            f"Unexpected error while fetching NSE constituents for {index_name}."
        ) from error


def choose_preferred_record(
    existing: InstrumentRecord | None,
    candidate: InstrumentRecord,
) -> InstrumentRecord:
    if existing is None:
        return candidate
    if existing.exchange == "BSE_EQ" and candidate.exchange == "NSE_EQ":
        return candidate
    return existing


async def fetch_equity_instruments() -> list[InstrumentRecord]:
    nse_content, bse_content = await asyncio.gather(
        fetch_bytes(NSE_INSTRUMENT_URL),
        fetch_bytes(BSE_INSTRUMENT_URL),
    )

    return parse_instrument_csv(nse_content) + parse_instrument_csv(bse_content)


async def persist_stock_instrument_keys(records: list[InstrumentRecord]) -> int:
    updates = [
        {
            "symbol": record.symbol,
            "instrument_key": record.instrument_key,
            "exchange": "NSE" if record.exchange == "NSE_EQ" else "BSE",
        }
        for record in records
        if record.exchange == "NSE_EQ"
    ]
    if not updates:
        return 0

    async with SessionLocal() as session:
        try:
            updated_count = 0
            for item in updates:
                statement = (
                    update(Stock)
                    .where(Stock.symbol == item["symbol"])
                    .values(
                        instrument_key=item["instrument_key"],
                        exchange=item["exchange"],
                    )
                )
                result = await session.execute(statement)
                updated_count += int(result.rowcount or 0)
            await session.commit()
        except Exception as error:
            await session.rollback()
            raise InstrumentSyncError("Unable to update stock instrument keys in PostgreSQL.") from error

    return updated_count


async def cache_instrument_maps(
    preferred_records: dict[str, InstrumentRecord],
    nifty50_symbols: list[str],
    nifty500_symbols: list[str],
    synced_at: str,
) -> InstrumentSyncSummary:
    redis_client = get_redis_client()
    symbol_to_key = {symbol: record.instrument_key for symbol, record in preferred_records.items()}
    key_to_symbol = {record.instrument_key: symbol for symbol, record in preferred_records.items()}
    meta_map = {symbol: record.to_meta_value() for symbol, record in preferred_records.items()}

    summary = InstrumentSyncSummary(
        synced_at=synced_at,
        symbol_count=len(symbol_to_key),
        reverse_count=len(key_to_symbol),
        nifty50_count=len(nifty50_symbols),
        nifty500_count=len(nifty500_symbols),
        preferred_exchange="NSE_EQ",
    )

    try:
        pipeline = redis_client.pipeline()
        pipeline.delete(
            SYMBOL_TO_KEY_HASH,
            KEY_TO_SYMBOL_HASH,
            SYMBOL_META_HASH,
            UNIVERSE_NIFTY50_KEY,
            UNIVERSE_NIFTY500_KEY,
            INSTRUMENT_SYNC_META_KEY,
        )
        if symbol_to_key:
            pipeline.hset(SYMBOL_TO_KEY_HASH, mapping=symbol_to_key)
            pipeline.expire(SYMBOL_TO_KEY_HASH, settings.redis_instrument_ttl_seconds)
        if key_to_symbol:
            pipeline.hset(KEY_TO_SYMBOL_HASH, mapping=key_to_symbol)
            pipeline.expire(KEY_TO_SYMBOL_HASH, settings.redis_instrument_ttl_seconds)
        if meta_map:
            pipeline.hset(SYMBOL_META_HASH, mapping=meta_map)
            pipeline.expire(SYMBOL_META_HASH, settings.redis_instrument_ttl_seconds)
        if nifty50_symbols:
            pipeline.sadd(UNIVERSE_NIFTY50_KEY, *nifty50_symbols)
            pipeline.expire(UNIVERSE_NIFTY50_KEY, settings.redis_instrument_ttl_seconds)
        if nifty500_symbols:
            pipeline.sadd(UNIVERSE_NIFTY500_KEY, *nifty500_symbols)
            pipeline.expire(UNIVERSE_NIFTY500_KEY, settings.redis_instrument_ttl_seconds)
        pipeline.hset(INSTRUMENT_SYNC_META_KEY, mapping=summary.to_redis_mapping())
        pipeline.expire(INSTRUMENT_SYNC_META_KEY, settings.redis_instrument_ttl_seconds)
        await pipeline.execute()
    except redis.RedisError as error:
        raise InstrumentSyncError("Unable to cache instrument maps in Redis.") from error

    return summary


async def sync_instruments_to_redis(update_database: bool = True) -> InstrumentSyncSummary:
    synced_at = datetime.now(tz=UTC).isoformat()
    try:
        instrument_rows, nifty50_symbols, nifty500_symbols = await asyncio.gather(
            fetch_equity_instruments(),
            fetch_index_members("NIFTY 50"),
            fetch_index_members("NIFTY 500"),
        )
    except InstrumentSyncError:
        raise
    except Exception as error:
        raise InstrumentSyncError("Unexpected error while collecting instrument inputs.") from error

    preferred_records: dict[str, InstrumentRecord] = {}
    for row in instrument_rows:
        preferred_records[row.symbol] = choose_preferred_record(
            preferred_records.get(row.symbol),
            row,
        )

    if update_database:
        await persist_stock_instrument_keys(list(preferred_records.values()))

    summary = await cache_instrument_maps(
        preferred_records=preferred_records,
        nifty50_symbols=nifty50_symbols,
        nifty500_symbols=nifty500_symbols,
        synced_at=synced_at,
    )
    return summary


async def get_instrument_sync_status() -> dict[str, str | int | bool]:
    redis_client = get_redis_client()

    try:
        metadata, symbol_count, reverse_count = await asyncio.gather(
            redis_client.hgetall(INSTRUMENT_SYNC_META_KEY),
            redis_client.hlen(SYMBOL_TO_KEY_HASH),
            redis_client.hlen(KEY_TO_SYMBOL_HASH),
        )
    except redis.RedisError as error:
        raise InstrumentSyncError("Unable to read the instrument sync status from Redis.") from error

    if not metadata:
        return {
            "ready": False,
            "symbol_count": 0,
            "reverse_count": 0,
        }

    return {
        "ready": True,
        "synced_at": metadata.get("synced_at", ""),
        "symbol_count": symbol_count,
        "reverse_count": reverse_count,
        "nifty50_count": int(metadata.get("nifty50_count", "0")),
        "nifty500_count": int(metadata.get("nifty500_count", "0")),
        "preferred_exchange": metadata.get("preferred_exchange", ""),
    }


async def get_symbol_to_key_map() -> dict[str, str]:
    redis_client = get_redis_client()
    try:
        return await redis_client.hgetall(SYMBOL_TO_KEY_HASH)
    except redis.RedisError as error:
        raise InstrumentSyncError("Unable to read the symbol to key map from Redis.") from error


async def get_key_to_symbol_map() -> dict[str, str]:
    redis_client = get_redis_client()
    try:
        return await redis_client.hgetall(KEY_TO_SYMBOL_HASH)
    except redis.RedisError as error:
        raise InstrumentSyncError("Unable to read the key to symbol map from Redis.") from error


async def get_universe_members(universe_key: str) -> list[str]:
    redis_client = get_redis_client()
    try:
        members = await redis_client.smembers(universe_key)
    except redis.RedisError as error:
        raise InstrumentSyncError(f"Unable to read Redis set {universe_key}.") from error

    return sorted(members)


@router.post("/sync")
async def sync_instruments(
    update_database: bool = Query(default=True),
) -> dict[str, str | int]:
    try:
        summary = await sync_instruments_to_redis(update_database=update_database)
    except InstrumentSyncError as error:
        logger.exception("instrument sync failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

    return asdict(summary)


@router.get("/status")
async def instrument_status() -> dict[str, str | int | bool]:
    try:
        return await get_instrument_sync_status()
    except InstrumentSyncError as error:
        logger.exception("instrument status lookup failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/nifty50")
async def instrument_nifty50() -> dict[str, object]:
    try:
        members = await get_universe_members(UNIVERSE_NIFTY50_KEY)
    except InstrumentSyncError as error:
        logger.exception("nifty50 lookup failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

    return {"count": len(members), "symbols": members}


@router.get("/nifty500")
async def instrument_nifty500() -> dict[str, object]:
    try:
        members = await get_universe_members(UNIVERSE_NIFTY500_KEY)
    except InstrumentSyncError as error:
        logger.exception("nifty500 lookup failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

    return {"count": len(members), "symbols": members}
