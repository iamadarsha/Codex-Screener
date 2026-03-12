"""Opening Range Breakout (ORB) detector.

Stores the high/low of the first 15-minute candle (09:15 -- 09:30 IST) in
Redis and checks whether the current price has broken above or below that
range.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import structlog

from app.services.redis_cache import get_redis
from app.utils.redis_keys import orb_range_key

log = structlog.get_logger(__name__)


def _to_decimal(value: object) -> Decimal | None:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


class ORBDetector:
    """Compute and query Opening Range Breakout levels via Redis."""

    def __init__(self) -> None:
        self._redis = get_redis()

    # ------------------------------------------------------------------
    # Set the opening range
    # ------------------------------------------------------------------

    async def set_opening_range(
        self,
        symbol: str,
        candles_9_15_to_9_30: list[dict],
    ) -> dict[str, str] | None:
        """Compute and store the ORB range for *symbol*.

        Parameters
        ----------
        symbol:
            NSE symbol (e.g. ``"RELIANCE"``).
        candles_9_15_to_9_30:
            One or more candle dicts covering 09:15-09:30.  Each must contain
            ``"high"`` and ``"low"`` keys.

        Returns
        -------
        dict or None
            ``{"high": ..., "low": ...}`` that was stored, or ``None`` on
            failure.
        """
        if not candles_9_15_to_9_30:
            log.warning("orb_no_candles", symbol=symbol)
            return None

        highs: list[Decimal] = []
        lows: list[Decimal] = []

        for c in candles_9_15_to_9_30:
            h = _to_decimal(c.get("high"))
            lo = _to_decimal(c.get("low"))
            if h is None or lo is None:
                log.warning("orb_bad_candle", symbol=symbol, candle=c)
                continue
            highs.append(h)
            lows.append(lo)

        if not highs:
            return None

        orb_high = max(highs)
        orb_low = min(lows)

        key = orb_range_key(symbol)
        mapping = {"high": str(orb_high), "low": str(orb_low)}
        await self._redis.hset(key, mapping=mapping)  # type: ignore[arg-type]
        # Expire at end of trading day (valid only for the session).
        await self._redis.expire(key, 8 * 60 * 60)

        log.info(
            "orb_range_set",
            symbol=symbol,
            high=str(orb_high),
            low=str(orb_low),
        )
        return mapping

    # ------------------------------------------------------------------
    # Check breakout
    # ------------------------------------------------------------------

    async def check_breakout(
        self,
        symbol: str,
        current_price: float | Decimal | str,
    ) -> str | None:
        """Check if *current_price* breaks the stored ORB range.

        Returns
        -------
        str or None
            ``"BULLISH"`` if price > ORB high, ``"BEARISH"`` if price < ORB
            low, or ``None`` if inside the range or data is unavailable.
        """
        price = _to_decimal(current_price)
        if price is None:
            return None

        key = orb_range_key(symbol)
        data = await self._redis.hgetall(key)

        if not data:
            log.debug("orb_no_range", symbol=symbol)
            return None

        orb_high = _to_decimal(data.get("high"))
        orb_low = _to_decimal(data.get("low"))
        if orb_high is None or orb_low is None:
            return None

        if price > orb_high:
            return "BULLISH"
        if price < orb_low:
            return "BEARISH"
        return None

    # ------------------------------------------------------------------
    # Convenience: fetch stored range
    # ------------------------------------------------------------------

    async def get_range(self, symbol: str) -> dict[str, str] | None:
        """Return the stored ORB range or ``None``."""
        data = await self._redis.hgetall(orb_range_key(symbol))
        return data if data else None
