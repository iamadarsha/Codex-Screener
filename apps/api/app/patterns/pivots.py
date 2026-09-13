"""Local high/low pivot detection — the shared geometry primitive every
structural pattern in `structural.py` is built on.

Pure function on a chronological candle list; no I/O, fully
synthetic-data-testable (mirrors the convention of `app.breakouts.levels`).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.patterns.types import Candle, Pivot, PivotKind

DEFAULT_PIVOT_WINDOW = 3


def _d(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot convert {value!r} to Decimal") from exc


def find_pivots(candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW) -> list[Pivot]:
    """Detect local high/low pivots over a rolling *window* on both sides.

    A candle at index *i* is a pivot high when its high is strictly greater
    than every candle's high within *window* bars on either side; a pivot
    low is the mirror image on lows. A single bar may register as both (a
    degenerate case, e.g. an isolated spike) — both are reported.

    Parameters
    ----------
    candles:
        Chronologically ordered (oldest first) candle dicts.
    window:
        Number of bars to compare against on each side. Must be >= 1.

    Returns
    -------
    list[Pivot]
        Pivots in chronological order (by index). Empty if there aren't
        enough candles to form even one full window.
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    n = len(candles)
    pivots: list[Pivot] = []
    if n < 2 * window + 1:
        return pivots

    for i in range(window, n - window):
        high_i = _d(candles[i]["high"])
        low_i = _d(candles[i]["low"])

        neighborhood = candles[i - window : i] + candles[i + 1 : i + window + 1]
        neighborhood_highs = [_d(c["high"]) for c in neighborhood]
        neighborhood_lows = [_d(c["low"]) for c in neighborhood]

        if all(high_i > h for h in neighborhood_highs):
            pivots.append(Pivot(index=i, price=high_i, kind=PivotKind.HIGH))
        if all(low_i < l for l in neighborhood_lows):
            pivots.append(Pivot(index=i, price=low_i, kind=PivotKind.LOW))

    return pivots


def pivot_highs(pivots: list[Pivot]) -> list[Pivot]:
    return [p for p in pivots if p.kind is PivotKind.HIGH]


def pivot_lows(pivots: list[Pivot]) -> list[Pivot]:
    return [p for p in pivots if p.kind is PivotKind.LOW]
