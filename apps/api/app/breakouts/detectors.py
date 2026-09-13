"""Pure raw-event classification for the breakout engine.

Every function here takes already-fetched data (no Redis/Postgres I/O) and
returns a `RawEvent` — fully unit-testable with synthetic candle lists.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.breakouts.types import Direction, RawEvent
from app.utils.decimals import safe_decimal


def classify_event(
    direction: Direction,
    level: Decimal,
    prev_value: Decimal | None,
    current_value: Decimal,
    was_triggered: bool,
) -> RawEvent:
    """Generic price-or-volume-vs-level classifier, reused across every
    trigger type — the level and values are just numbers to this function.

    On a tracker's very first evaluation (`prev_value is None`, i.e. no
    prior observation exists yet — a fresh tracker, or one just re-armed
    after a restart), a value already beyond the level counts as a cross
    too: we have no evidence it was ever inside the range, and silently
    never detecting a breakout that was already in progress before the
    engine's first look (e.g. a gap-up past PDH before cold start caught
    up) would be worse than treating first-observation-already-through as
    the same signal a live cross would have produced.
    """
    if direction is Direction.BULLISH:
        crossed = (prev_value is None or prev_value <= level) and current_value > level
        holding = current_value > level
    else:
        crossed = (prev_value is None or prev_value >= level) and current_value < level
        holding = current_value < level

    if was_triggered and not holding:
        return RawEvent.REVERSE
    if was_triggered and holding:
        return RawEvent.HOLD
    if crossed:
        return RawEvent.CROSS_UP if direction is Direction.BULLISH else RawEvent.CROSS_DOWN
    return RawEvent.NONE


def classify_series_cross(
    prev_a: Decimal | None,
    prev_b: Decimal | None,
    cur_a: Decimal | None,
    cur_b: Decimal | None,
) -> RawEvent:
    """Two-series crossover (EMA9/EMA21, MACD/signal) — mirrors
    `app.screener.dsl.evaluator._eval_cross`'s semantics: bullish cross is
    `prev_a <= prev_b and cur_a > cur_b`.

    Unlike `classify_event`, this has no persistent "was_triggered" concept
    of its own — HOLD/REVERSE for series crosses is handled by the state
    machine treating the cross itself as the level (see `levels.py`'s
    `ema_cross_level`/`macd_cross_level`, which re-derive a synthetic
    reference level from the crossing series so `classify_event` can still
    drive confirmation/reversal uniformly).
    """
    if None in (prev_a, prev_b, cur_a, cur_b):
        return RawEvent.NONE
    if prev_a <= prev_b and cur_a > cur_b:
        return RawEvent.CROSS_UP
    if prev_a >= prev_b and cur_a < cur_b:
        return RawEvent.CROSS_DOWN
    return RawEvent.NONE


def narrowest_range_bar(candles: list[dict[str, Any]], n: int) -> dict[str, Any] | None:
    """Return the most-recently-completed bar if its (high-low) range is the
    narrowest of the last *n* completed bars (NR4: n=4, NR7: n=7) — else None.

    *candles* must be oldest-first, with the last element being the most
    recently completed bar (never the still-forming current bar).
    """
    if len(candles) < n:
        return None
    window = candles[-n:]
    ranges = [safe_decimal(c["high"]) - safe_decimal(c["low"]) for c in window]
    if any(r is None for r in ranges):
        return None
    last_range = ranges[-1]
    if last_range == min(ranges):
        return window[-1]
    return None


def is_inside_bar(prev_bar: dict[str, Any], current_bar: dict[str, Any]) -> bool:
    """True when *current_bar* is strictly contained within *prev_bar*'s range."""
    ph, pl = safe_decimal(prev_bar["high"]), safe_decimal(prev_bar["low"])
    ch, cl = safe_decimal(current_bar["high"]), safe_decimal(current_bar["low"])
    if None in (ph, pl, ch, cl):
        return False
    return ch <= ph and cl >= pl


def bollinger_bandwidth(upper: Decimal | None, lower: Decimal | None, mid: Decimal | None) -> float | None:
    if upper is None or lower is None or mid is None or mid == 0:
        return None
    return float((upper - lower) / mid)


def is_bollinger_squeeze(bandwidth_history: list[float], current_bandwidth: float | None) -> bool:
    """True when *current_bandwidth* is in the bottom 20th percentile of the
    supplied rolling history — a simple, explicit squeeze definition (no ML).
    """
    if current_bandwidth is None or len(bandwidth_history) < 5:
        return False
    sorted_history = sorted(bandwidth_history)
    cutoff_idx = max(0, int(len(sorted_history) * 0.2) - 1)
    return current_bandwidth <= sorted_history[cutoff_idx]
