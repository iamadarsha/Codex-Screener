"""Per-trigger-type reference level computation.

All functions here are pure (no Redis/Postgres I/O) and take already-fetched
data, so they're fully unit-testable with synthetic candle lists — with one
deliberate exception: `orb_levels()`, which needs `ORBDetector`'s existing
Redis-backed opening-range storage (see module docstring below for why it's
reused rather than reimplemented).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.breakouts.detectors import is_inside_bar, narrowest_range_bar
from app.breakouts.types import Direction, ReferenceLevel, TriggerType
from app.services.orb import ORBDetector
from app.utils.decimals import safe_decimal

DEFAULT_DONCHIAN_LENGTH = 20
DEFAULT_VOLUME_MULTIPLIER = 2.0

_orb_detector = ORBDetector()


def pdh_pdl_levels(ind_1d: dict[str, Any]) -> list[ReferenceLevel]:
    """Previous-day high/low, from the daily indicator hash's existing
    `prev_high`/`prev_low` fields (written by `YFinanceProvider.bulk_compute`).
    """
    levels: list[ReferenceLevel] = []
    pdh = safe_decimal(ind_1d.get("prev_high"))
    pdl = safe_decimal(ind_1d.get("prev_low"))
    if pdh is not None:
        levels.append(ReferenceLevel(TriggerType.PDH_PDL, Direction.BULLISH, pdh))
    if pdl is not None:
        levels.append(ReferenceLevel(TriggerType.PDH_PDL, Direction.BEARISH, pdl))
    return levels


def fifty_two_week_levels(ind_1d: dict[str, Any]) -> list[ReferenceLevel]:
    """52-week high/low — from `ind_1d`'s true 252-day-lookback fields, NOT
    `SymbolIndicatorState.high_52w` (which is a bounded ~210-bar intraday
    running max and would silently under-report a true 52-week extreme).
    """
    levels: list[ReferenceLevel] = []
    high = safe_decimal(ind_1d.get("high_52w"))
    low = safe_decimal(ind_1d.get("low_52w"))
    if high is not None:
        levels.append(ReferenceLevel(TriggerType.FIFTY_TWO_WEEK, Direction.BULLISH, high))
    if low is not None:
        levels.append(ReferenceLevel(TriggerType.FIFTY_TWO_WEEK, Direction.BEARISH, low))
    return levels


def donchian_levels(
    completed_candles: list[dict[str, Any]], length: int = DEFAULT_DONCHIAN_LENGTH,
) -> list[ReferenceLevel]:
    """Donchian channel high/low over the last *length* completed bars.

    *completed_candles* must exclude the still-forming current bar.
    """
    if len(completed_candles) < length:
        return []
    window = completed_candles[-length:]
    highs = [safe_decimal(c["high"]) for c in window]
    lows = [safe_decimal(c["low"]) for c in window]
    if any(h is None for h in highs) or any(low is None for low in lows):
        return []
    return [
        ReferenceLevel(TriggerType.DONCHIAN, Direction.BULLISH, max(highs), {"length": length}),
        ReferenceLevel(TriggerType.DONCHIAN, Direction.BEARISH, min(lows), {"length": length}),
    ]


def nr_levels(completed_candles: list[dict[str, Any]], n: int) -> list[ReferenceLevel]:
    """NR4 (n=4) / NR7 (n=7): bilateral levels at the narrowest-of-last-n
    bar's high/low, only present the cycle that bar completes.
    """
    trigger_type = TriggerType.NR4 if n == 4 else TriggerType.NR7
    bar = narrowest_range_bar(completed_candles, n)
    if bar is None:
        return []
    high, low = safe_decimal(bar["high"]), safe_decimal(bar["low"])
    if high is None or low is None:
        return []
    return [
        ReferenceLevel(trigger_type, Direction.BULLISH, high),
        ReferenceLevel(trigger_type, Direction.BEARISH, low),
    ]


def inside_bar_levels(completed_candles: list[dict[str, Any]]) -> list[ReferenceLevel]:
    """Bilateral levels at the inside bar's own high/low — breakout beyond
    the (tighter) inside bar's range confirms continuation."""
    if len(completed_candles) < 2:
        return []
    prev_bar, current_bar = completed_candles[-2], completed_candles[-1]
    if not is_inside_bar(prev_bar, current_bar):
        return []
    high, low = safe_decimal(current_bar["high"]), safe_decimal(current_bar["low"])
    if high is None or low is None:
        return []
    return [
        ReferenceLevel(TriggerType.INSIDE_BAR, Direction.BULLISH, high),
        ReferenceLevel(TriggerType.INSIDE_BAR, Direction.BEARISH, low),
    ]


def volume_breakout_level(
    ind_1d: dict[str, Any], multiplier: float = DEFAULT_VOLUME_MULTIPLIER,
) -> ReferenceLevel | None:
    """Volume breakout is inherently one-directional (a spike, not a dip) —
    level = avg 20-day volume x multiplier; the "price" compared against it
    (fed in by the caller) is the current bar's volume, not its price."""
    avg_volume = safe_decimal(ind_1d.get("sma_20_volume"))
    if avg_volume is None:
        return None
    return ReferenceLevel(
        TriggerType.VOLUME_BREAKOUT, Direction.BULLISH, avg_volume * Decimal(str(multiplier)),
        {"multiplier": multiplier},
    )


def vwap_levels(ind_live: dict[str, Any]) -> list[ReferenceLevel]:
    """Same VWAP value, both directions: BULLISH = reclaim (crossing up
    through VWAP), BEARISH = breakdown (crossing down through VWAP)."""
    vwap = safe_decimal(ind_live.get("vwap"))
    if vwap is None:
        return []
    return [
        ReferenceLevel(TriggerType.VWAP, Direction.BULLISH, vwap),
        ReferenceLevel(TriggerType.VWAP, Direction.BEARISH, vwap),
    ]


def ema_cross_reference(ind_live: dict[str, Any]) -> Decimal | None:
    """Informational reference level for display (BreakoutSignal.reference_level)
    on an EMA9/EMA21 cross — the actual event classification is a zero-cross
    of (ema_9 - ema_21), computed by the caller via `classify_event` with
    `level=Decimal(0)` (see `engine.py`), not this value."""
    return safe_decimal(ind_live.get("ema_21"))


def macd_cross_reference(ind_live: dict[str, Any]) -> Decimal | None:
    return safe_decimal(ind_live.get("macd_signal"))


async def orb_levels(symbol: str, first_15min_candle: dict[str, Any] | None) -> list[ReferenceLevel]:
    """Opening-range high/low, via the existing `ORBDetector` (reused, not
    reimplemented) — this call also *writes* `orb:{symbol}:range` once per
    session, which fixes `screener_engine.py`'s ORB scan filter (previously
    always reading an empty hash, since nothing ever called
    `set_opening_range()` in production).
    """
    if first_15min_candle is not None:
        await _orb_detector.set_opening_range(symbol, [first_15min_candle])
    range_data = await _orb_detector.get_range(symbol)
    if not range_data:
        return []
    high, low = safe_decimal(range_data.get("high")), safe_decimal(range_data.get("low"))
    if high is None or low is None:
        return []
    return [
        ReferenceLevel(TriggerType.ORB, Direction.BULLISH, high),
        ReferenceLevel(TriggerType.ORB, Direction.BEARISH, low),
    ]
