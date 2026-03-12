"""Real-time candle aggregation from WebSocket ticks."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from app.db.models.ohlcv import Ohlcv1Min
from app.db.session import SessionLocal
from app.services.redis_cache import get_redis, hget_all, hset_dict
from app.utils.decimals import safe_decimal
from app.utils.redis_keys import TTL_CANDLE_CURRENT, candle_current_key
from app.utils.time import IST, get_candle_boundary

log = structlog.get_logger(__name__)

_TIMEFRAMES = ("1min", "5min", "15min")


class CandleBuilder:
    """Aggregates tick data into OHLCV candles across multiple timeframes.

    Current (in-progress) candles are stored in Redis hashes.  When a tick
    falls outside the current candle boundary a new candle is started and
    the completed candle is returned to the caller for downstream processing.
    """

    async def on_tick(
        self,
        symbol: str,
        ltp: float,
        volume: int,
        ts: datetime,
    ) -> list[dict[str, Any]]:
        """Process a single market tick.

        Returns a list of completed candle dicts (one per timeframe that
        rolled over).  Completed 1-min candles are also persisted to the
        database.
        """
        completed: list[dict[str, Any]] = []

        for tf in _TIMEFRAMES:
            boundary = get_candle_boundary(ts, tf)
            key = candle_current_key(symbol, tf)
            candle = await self._get_current(key)

            if candle is None or candle["boundary"] != boundary.isoformat():
                # The candle slot changed -- finalise the old one (if any)
                if candle is not None:
                    done = self._finalise(candle, symbol, tf)
                    completed.append(done)
                    if tf == "1min":
                        await self._persist_1min(done)

                # Start a fresh candle
                candle = self._new_candle(boundary, ltp, volume)
            else:
                # Update in-flight candle
                candle = self._update(candle, ltp, volume)

            await self._save_current(key, candle)

        return completed

    # ------------------------------------------------------------------
    # Internal helpers
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

    @staticmethod
    async def _persist_1min(candle: dict[str, Any]) -> None:
        """Insert a completed 1-min candle into the ``ohlcv_1min`` table."""
        try:
            ts = datetime.fromisoformat(candle["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=IST)

            row = Ohlcv1Min(
                symbol=candle["symbol"],
                ts=ts,
                open=safe_decimal(candle["open"], Decimal(0)),
                high=safe_decimal(candle["high"], Decimal(0)),
                low=safe_decimal(candle["low"], Decimal(0)),
                close=safe_decimal(candle["close"], Decimal(0)),
                volume=candle["volume"],
            )
            async with SessionLocal() as session:
                session.add(row)
                await session.commit()
        except Exception:
            log.exception("candle_persist_failed", candle=candle)
