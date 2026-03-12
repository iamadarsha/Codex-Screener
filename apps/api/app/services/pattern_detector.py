"""Candlestick pattern detection using Decimal-safe comparisons."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TypedDict

import structlog

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
class Candle(TypedDict, total=False):
    open: str | float | Decimal
    high: str | float | Decimal
    low: str | float | Decimal
    close: str | float | Decimal
    volume: str | float | Decimal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d(value: object) -> Decimal:
    """Coerce to Decimal; raises ValueError on failure."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot convert {value!r} to Decimal") from exc


def _body(candle: Candle) -> Decimal:
    """Absolute body size."""
    return abs(_d(candle["close"]) - _d(candle["open"]))


def _range(candle: Candle) -> Decimal:
    """High - Low range."""
    return _d(candle["high"]) - _d(candle["low"])


def _is_bullish(candle: Candle) -> bool:
    return _d(candle["close"]) > _d(candle["open"])


def _is_bearish(candle: Candle) -> bool:
    return _d(candle["close"]) < _d(candle["open"])


def _upper_shadow(candle: Candle) -> Decimal:
    return _d(candle["high"]) - max(_d(candle["open"]), _d(candle["close"]))


def _lower_shadow(candle: Candle) -> Decimal:
    return min(_d(candle["open"]), _d(candle["close"])) - _d(candle["low"])


# ---------------------------------------------------------------------------
# Individual pattern detectors
# ---------------------------------------------------------------------------

def _is_doji(candle: Candle) -> bool:
    """Body is less than 10 % of total range."""
    rng = _range(candle)
    if rng == 0:
        return True
    return _body(candle) / rng < Decimal("0.1")


def _is_hammer(candle: Candle) -> bool:
    """Small body in upper quarter; lower shadow >= 2x body."""
    body = _body(candle)
    if body == 0:
        return False
    lower = _lower_shadow(candle)
    upper = _upper_shadow(candle)
    return lower >= 2 * body and upper <= body


def _is_engulfing_bullish(prev: Candle, curr: Candle) -> bool:
    """Current bullish candle fully engulfs previous bearish candle body."""
    if not (_is_bearish(prev) and _is_bullish(curr)):
        return False
    return (
        _d(curr["open"]) <= _d(prev["close"])
        and _d(curr["close"]) >= _d(prev["open"])
    )


def _is_engulfing_bearish(prev: Candle, curr: Candle) -> bool:
    """Current bearish candle fully engulfs previous bullish candle body."""
    if not (_is_bullish(prev) and _is_bearish(curr)):
        return False
    return (
        _d(curr["open"]) >= _d(prev["close"])
        and _d(curr["close"]) <= _d(prev["open"])
    )


def _is_morning_star(c1: Candle, c2: Candle, c3: Candle) -> bool:
    """Three-bar bullish reversal: bearish -> small body -> bullish."""
    if not _is_bearish(c1):
        return False
    if _body(c2) >= _body(c1) * Decimal("0.3"):
        return False
    if not _is_bullish(c3):
        return False
    mid = (_d(c1["open"]) + _d(c1["close"])) / 2
    return _d(c3["close"]) > mid


def _is_evening_star(c1: Candle, c2: Candle, c3: Candle) -> bool:
    """Three-bar bearish reversal: bullish -> small body -> bearish."""
    if not _is_bullish(c1):
        return False
    if _body(c2) >= _body(c1) * Decimal("0.3"):
        return False
    if not _is_bearish(c3):
        return False
    mid = (_d(c1["open"]) + _d(c1["close"])) / 2
    return _d(c3["close"]) < mid


def _is_three_white_soldiers(c1: Candle, c2: Candle, c3: Candle) -> bool:
    """Three consecutive bullish candles, each opening within the prior body."""
    for c in (c1, c2, c3):
        if not _is_bullish(c):
            return False
    return (
        _d(c2["open"]) > _d(c1["open"])
        and _d(c2["close"]) > _d(c1["close"])
        and _d(c3["open"]) > _d(c2["open"])
        and _d(c3["close"]) > _d(c2["close"])
    )


def _is_three_black_crows(c1: Candle, c2: Candle, c3: Candle) -> bool:
    """Three consecutive bearish candles, each opening within the prior body."""
    for c in (c1, c2, c3):
        if not _is_bearish(c):
            return False
    return (
        _d(c2["open"]) < _d(c1["open"])
        and _d(c2["close"]) < _d(c1["close"])
        and _d(c3["open"]) < _d(c2["open"])
        and _d(c3["close"]) < _d(c2["close"])
    )


def _is_harami_bullish(prev: Candle, curr: Candle) -> bool:
    """Small bullish body contained within prior bearish body."""
    if not (_is_bearish(prev) and _is_bullish(curr)):
        return False
    return (
        _d(curr["open"]) >= _d(prev["close"])
        and _d(curr["close"]) <= _d(prev["open"])
    )


def _is_harami_bearish(prev: Candle, curr: Candle) -> bool:
    """Small bearish body contained within prior bullish body."""
    if not (_is_bullish(prev) and _is_bearish(curr)):
        return False
    return (
        _d(curr["open"]) <= _d(prev["close"])
        and _d(curr["close"]) >= _d(prev["open"])
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_patterns(candles: list[Candle]) -> list[str]:
    """Detect candlestick patterns in the most recent candles.

    Parameters
    ----------
    candles:
        Chronologically ordered list of candle dicts (oldest first).
        At least 1 candle is required; 3 candles enables all patterns.

    Returns
    -------
    list[str]
        Names of all detected patterns (may be empty).
    """
    patterns: list[str] = []

    if not candles:
        return patterns

    try:
        latest = candles[-1]

        # --- single-candle patterns ---
        if _is_doji(latest):
            patterns.append("doji")
        if _is_hammer(latest):
            patterns.append("hammer")

        # --- two-candle patterns ---
        if len(candles) >= 2:
            prev = candles[-2]
            if _is_engulfing_bullish(prev, latest):
                patterns.append("engulfing_bullish")
            if _is_engulfing_bearish(prev, latest):
                patterns.append("engulfing_bearish")
            if _is_harami_bullish(prev, latest):
                patterns.append("harami_bullish")
            if _is_harami_bearish(prev, latest):
                patterns.append("harami_bearish")

        # --- three-candle patterns ---
        if len(candles) >= 3:
            c1, c2, c3 = candles[-3], candles[-2], candles[-1]
            if _is_morning_star(c1, c2, c3):
                patterns.append("morning_star")
            if _is_evening_star(c1, c2, c3):
                patterns.append("evening_star")
            if _is_three_white_soldiers(c1, c2, c3):
                patterns.append("three_white_soldiers")
            if _is_three_black_crows(c1, c2, c3):
                patterns.append("three_black_crows")

    except (KeyError, ValueError) as exc:
        log.warning("pattern_detection_error", error=str(exc))

    return patterns
