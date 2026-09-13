"""Session-aware candle aggregation with batched persistence.

Supersedes `app.services.candle_builder.CandleBuilder`: reuses the same
Redis-hash-per-symbol+timeframe current-candle store, but completed
1-minute candles are buffered in-process and flushed in a single bulk
upsert on a size threshold, instead of one DB transaction per candle
(the Phase 1-audited persistence bug). Persistence failures are raised to
the caller — who logs with full context and can alert — rather than
silently swallowed.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models.ohlcv import Ohlcv1Min, OhlcvDaily
from app.db.session import SessionLocal
from app.services.redis_cache import hget_all, hset_dict
from app.utils.decimals import safe_decimal
from app.utils.redis_keys import TTL_CANDLE_CURRENT, candle_current_key
from app.utils.time import IST, get_candle_boundary

log = structlog.get_logger(__name__)

TIMEFRAMES = ("1min", "5min", "15min")

_FLUSH_BATCH_SIZE = 200

# Minimum number of candles required to compute the slowest indicator (SMA-200)
_HISTORY_CANDLE_LIMIT = 210


async def fetch_candle_history(symbol: str, timeframe: str) -> list[dict[str, Any]]:
    """Load recent candles from Postgres, oldest-first.

    Moved here from the now-deleted `app.services.indicator_engine` (Phase
    2.2) — this was the one piece of that module still in active use, via
    `screener_engine.py`'s DSL historical-offset/rolling-function fetches.
    """
    from sqlalchemy import select

    async with SessionLocal() as session:
        if timeframe in ("1min", "5min", "15min"):
            stmt = (
                select(Ohlcv1Min)
                .where(Ohlcv1Min.symbol == symbol)
                .order_by(Ohlcv1Min.ts.desc())
                .limit(_HISTORY_CANDLE_LIMIT)
            )
            rows = (await session.execute(stmt)).scalars().all()
        else:
            stmt = (
                select(OhlcvDaily)
                .where(OhlcvDaily.symbol == symbol)
                .order_by(OhlcvDaily.date.desc())
                .limit(_HISTORY_CANDLE_LIMIT)
            )
            rows = (await session.execute(stmt)).scalars().all()

    candles: list[dict[str, Any]] = [
        {
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": int(r.volume),
        }
        for r in reversed(rows)
    ]
    return candles


class CandlePersistenceError(Exception):
    """Raised when a batch of completed candles fails to persist."""


class CandleEngine:
    """Aggregates ticks into multi-timeframe OHLCV candles.

    Callers get completed candles back from `on_tick` immediately for
    pushing onto the event bus / in-memory state; 1-minute candles are
    also queued for batched database persistence via `flush_pending()`.
    """

    def __init__(self) -> None:
        self._pending_1min: list[dict[str, Any]] = []
        self._flush_lock = asyncio.Lock()

    async def on_tick(
        self,
        symbol: str,
        ltp: float,
        volume_delta: int,
        ts: datetime,
    ) -> list[dict[str, Any]]:
        """Process one tick's price + **delta** volume (e.g. `ltq`, never `vtt`).

        Returns completed candle dicts, one per timeframe that rolled over.
        """
        completed: list[dict[str, Any]] = []

        for tf in TIMEFRAMES:
            boundary = get_candle_boundary(ts, tf)
            key = candle_current_key(symbol, tf)
            candle = await self._get_current(key)

            if candle is None or candle["boundary"] != boundary.isoformat():
                if candle is not None:
                    done = self._finalise(candle, symbol, tf)
                    completed.append(done)
                    if tf == "1min":
                        self._pending_1min.append(done)
                candle = self._new_candle(boundary, ltp, volume_delta)
            else:
                candle = self._update(candle, ltp, volume_delta)

            await self._save_current(key, candle)

        if len(self._pending_1min) >= _FLUSH_BATCH_SIZE:
            await self.flush_pending()

        return completed

    async def flush_pending(self) -> int:
        """Bulk-upsert any buffered 1-minute candles. Returns rows written.

        Raises `CandlePersistenceError` on failure (and puts the batch back
        for a later retry) instead of swallowing it — the old
        `CandleBuilder._persist_1min` logged and dropped failed writes.
        """
        async with self._flush_lock:
            if not self._pending_1min:
                return 0
            batch, self._pending_1min = self._pending_1min, []

        rows = []
        for candle in batch:
            ts = datetime.fromisoformat(candle["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=IST)
            rows.append(
                {
                    "symbol": candle["symbol"],
                    "ts": ts,
                    "open": safe_decimal(candle["open"], Decimal(0)),
                    "high": safe_decimal(candle["high"], Decimal(0)),
                    "low": safe_decimal(candle["low"], Decimal(0)),
                    "close": safe_decimal(candle["close"], Decimal(0)),
                    "volume": candle["volume"],
                }
            )

        try:
            async with SessionLocal() as session:
                stmt = pg_insert(Ohlcv1Min).values(rows)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "ts"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                    },
                )
                await session.execute(stmt)
                await session.commit()
        except Exception as exc:
            async with self._flush_lock:
                self._pending_1min = batch + self._pending_1min
            log.error("candle_batch_persist_failed", count=len(rows), error=str(exc))
            raise CandlePersistenceError(f"failed to persist {len(rows)} candles") from exc

        log.debug("candle_batch_persisted", count=len(rows))
        return len(rows)

    def pending_count(self) -> int:
        return len(self._pending_1min)

    # ------------------------------------------------------------------
    # Internal helpers — candle arithmetic ported from CandleBuilder
    # ------------------------------------------------------------------

    @staticmethod
    def _new_candle(boundary: datetime, ltp: float, volume: int) -> dict[str, Any]:
        return {
            "boundary": boundary.isoformat(),
            "open": str(ltp),
            "high": str(ltp),
            "low": str(ltp),
            "close": str(ltp),
            "volume": str(volume),
        }

    @staticmethod
    def _update(candle: dict[str, Any], ltp: float, volume: int) -> dict[str, Any]:
        price = Decimal(str(ltp))
        candle["close"] = str(price)
        if price > Decimal(candle["high"]):
            candle["high"] = str(price)
        if price < Decimal(candle["low"]):
            candle["low"] = str(price)
        candle["volume"] = str(int(candle["volume"]) + volume)
        return candle

    @staticmethod
    def _finalise(candle: dict[str, Any], symbol: str, tf: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "timeframe": tf,
            "ts": candle["boundary"],
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "volume": int(candle["volume"]),
        }

    @staticmethod
    async def _get_current(key: str) -> dict[str, Any] | None:
        data = await hget_all(key)
        return data if data else None

    @staticmethod
    async def _save_current(key: str, candle: dict[str, Any]) -> None:
        await hset_dict(key, candle, ttl=TTL_CANDLE_CURRENT)
