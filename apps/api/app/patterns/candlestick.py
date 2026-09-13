"""Candlestick pattern detection using Decimal-safe comparisons.

Ported from the former `app.services.pattern_detector` (single-file, string
results, no confidence). Detection predicates are unchanged; each pattern
now also computes a confidence heuristic (0-1) from the same Decimal
measurements instead of a hardcoded 1.0, and results are returned as
`PatternMatch` objects carrying direction/support/resistance metadata.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import structlog

from app.patterns.types import Candle, PatternDirection, PatternMatch

log = structlog.get_logger(__name__)


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


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


# ---------------------------------------------------------------------------
# Single-candle patterns
# ---------------------------------------------------------------------------

def _is_doji(candle: Candle) -> bool:
    """Body is less than 10 % of total range."""
    rng = _range(candle)
    if rng == 0:
        return True
    return _body(candle) / rng < Decimal("0.1")


def _doji_confidence(candle: Candle) -> float:
    """Smaller body/range ratio -> higher confidence; a zero-range bar is a
    perfect (if degenerate) doji."""
    rng = _range(candle)
    if rng == 0:
        return 1.0
    ratio = _body(candle) / rng
    return _clamp01(float(1 - ratio / Decimal("0.1")))


def _is_hammer(candle: Candle) -> bool:
    """Small body in upper quarter; lower shadow >= 2x body."""
    body = _body(candle)
    if body == 0:
        return False
    lower = _lower_shadow(candle)
    upper = _upper_shadow(candle)
    return lower >= 2 * body and upper <= body


def _hammer_confidence(candle: Candle) -> float:
    """Longer lower shadow relative to body, and a smaller upper shadow,
    both strengthen the signal."""
    body = _body(candle)
    if body == 0:
        return 0.0
    lower = _lower_shadow(candle)
    upper = _upper_shadow(candle)
    shadow_strength = float(lower / body) / 4.0  # 4x body -> full strength
    upper_penalty = float(upper / body) * 0.25
    return _clamp01(shadow_strength - upper_penalty)


# ---------------------------------------------------------------------------
# Two-candle patterns
# ---------------------------------------------------------------------------

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


def _engulfing_confidence(prev: Candle, curr: Candle) -> float:
    """Larger current body relative to the prior body -> stronger engulf."""
    prev_body = _body(prev)
    curr_body = _body(curr)
    if prev_body == 0:
        return 1.0 if curr_body > 0 else 0.0
    ratio = curr_body / prev_body  # >= 1 by definition of engulfing
    return _clamp01(float(ratio) / 2.0)  # 2x the prior body -> full strength


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


def _harami_confidence(prev: Candle, curr: Candle) -> float:
    """Smaller current body relative to the prior body -> stronger harami
    (the "harami" reversal reads as more decisive the tighter the inside
    body is)."""
    prev_body = _body(prev)
    curr_body = _body(curr)
    if prev_body == 0:
        return 0.5  # degenerate: both bodies collapsed to zero
    ratio = curr_body / prev_body  # <= 1 by definition of containment
    return _clamp01(float(1 - ratio))


# ---------------------------------------------------------------------------
# Three-candle patterns
# ---------------------------------------------------------------------------

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


def _star_confidence(c1: Candle, c2: Candle, c3: Candle) -> float:
    """Averages two independent strength signals: how small the middle
    (indecision) candle's body is relative to the first candle, and how far
    the third candle's close penetrates into (or past) the first candle's
    body."""
    body1 = _body(c1)
    if body1 == 0:
        return 0.5
    small_body_ratio = _clamp01(float(1 - _body(c2) / body1))
    mid = (_d(c1["open"]) + _d(c1["close"])) / 2
    penetration = abs(_d(c3["close"]) - mid) / body1
    penetration_ratio = _clamp01(float(penetration))
    return _clamp01((small_body_ratio + penetration_ratio) / 2.0)


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


def _trio_conviction_confidence(c1: Candle, c2: Candle, c3: Candle) -> float:
    """Three-soldiers/crows conviction: average body/range ratio across the
    three candles — decisive candles with small shadows read as a stronger
    continuation signal than ones with long wicks."""
    ratios: list[float] = []
    for c in (c1, c2, c3):
        rng = _range(c)
        if rng == 0:
            ratios.append(0.0)
            continue
        ratios.append(float(_body(c) / rng))
    return _clamp01(sum(ratios) / len(ratios))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_candlestick_patterns(candles: list[Candle]) -> list[PatternMatch]:
    """Detect candlestick patterns in the most recent candles.

    Parameters
    ----------
    candles:
        Chronologically ordered list of candle dicts (oldest first).
        At least 1 candle is required; 3 candles enables all patterns.

    Returns
    -------
    list[PatternMatch]
        All detected patterns (may be empty).
    """
    matches: list[PatternMatch] = []

    if not candles:
        return matches

    try:
        latest = candles[-1]

        # --- single-candle patterns ---
        if _is_doji(latest):
            matches.append(
                PatternMatch(
                    name="doji",
                    confidence=_doji_confidence(latest),
                    direction=PatternDirection.NEUTRAL,
                )
            )
        if _is_hammer(latest):
            matches.append(
                PatternMatch(
                    name="hammer",
                    confidence=_hammer_confidence(latest),
                    direction=PatternDirection.BULLISH,
                    support=_d(latest["low"]),
                )
            )

        # --- two-candle patterns ---
        if len(candles) >= 2:
            prev = candles[-2]
            if _is_engulfing_bullish(prev, latest):
                matches.append(
                    PatternMatch(
                        name="engulfing_bullish",
                        confidence=_engulfing_confidence(prev, latest),
                        direction=PatternDirection.BULLISH,
                        support=min(_d(prev["low"]), _d(latest["low"])),
                    )
                )
            if _is_engulfing_bearish(prev, latest):
                matches.append(
                    PatternMatch(
                        name="engulfing_bearish",
                        confidence=_engulfing_confidence(prev, latest),
                        direction=PatternDirection.BEARISH,
                        resistance=max(_d(prev["high"]), _d(latest["high"])),
                    )
                )
            if _is_harami_bullish(prev, latest):
                matches.append(
                    PatternMatch(
                        name="harami_bullish",
                        confidence=_harami_confidence(prev, latest),
                        direction=PatternDirection.BULLISH,
                        support=_d(prev["low"]),
                    )
                )
            if _is_harami_bearish(prev, latest):
                matches.append(
                    PatternMatch(
                        name="harami_bearish",
                        confidence=_harami_confidence(prev, latest),
                        direction=PatternDirection.BEARISH,
                        resistance=_d(prev["high"]),
                    )
                )

        # --- three-candle patterns ---
        if len(candles) >= 3:
            c1, c2, c3 = candles[-3], candles[-2], candles[-1]
            if _is_morning_star(c1, c2, c3):
                matches.append(
                    PatternMatch(
                        name="morning_star",
                        confidence=_star_confidence(c1, c2, c3),
                        direction=PatternDirection.BULLISH,
                        support=min(_d(c1["low"]), _d(c2["low"]), _d(c3["low"])),
                    )
                )
            if _is_evening_star(c1, c2, c3):
                matches.append(
                    PatternMatch(
                        name="evening_star",
                        confidence=_star_confidence(c1, c2, c3),
                        direction=PatternDirection.BEARISH,
                        resistance=max(_d(c1["high"]), _d(c2["high"]), _d(c3["high"])),
                    )
                )
            if _is_three_white_soldiers(c1, c2, c3):
                matches.append(
                    PatternMatch(
                        name="three_white_soldiers",
                        confidence=_trio_conviction_confidence(c1, c2, c3),
                        direction=PatternDirection.BULLISH,
                        support=_d(c1["low"]),
                    )
                )
            if _is_three_black_crows(c1, c2, c3):
                matches.append(
                    PatternMatch(
                        name="three_black_crows",
                        confidence=_trio_conviction_confidence(c1, c2, c3),
                        direction=PatternDirection.BEARISH,
                        resistance=_d(c1["high"]),
                    )
                )

    except (KeyError, ValueError) as exc:
        log.warning("candlestick_pattern_detection_error", error=str(exc))

    return matches
