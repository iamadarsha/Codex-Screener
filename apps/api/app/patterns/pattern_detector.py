"""Thin façade combining candlestick + structural pattern detection.

Kept as a single, stable entry point (`detect_patterns`) so callers — today
just `app.services.screener_engine` — don't need to know about the
candlestick/structural package split.
"""

from __future__ import annotations

from app.patterns.candlestick import detect_candlestick_patterns
from app.patterns.structural import detect_structural_patterns
from app.patterns.types import Candle, PatternMatch


def detect_patterns(candles: list[Candle]) -> list[PatternMatch]:
    """Detect every supported candlestick and structural pattern.

    Parameters
    ----------
    candles:
        Chronologically ordered (oldest first) candle list. Candlestick
        patterns need as few as 1-3 candles; structural patterns need a
        much longer history to form pivots and only fire once enough
        candles are supplied.

    Returns
    -------
    list[PatternMatch]
        All detected patterns (may be empty).
    """
    return detect_candlestick_patterns(candles) + detect_structural_patterns(candles)
