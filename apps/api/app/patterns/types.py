"""Pure data types for the pattern engine — no logic, mirrors the role
`app.breakouts.types` plays for the breakout engine.

A local `PatternDirection` enum is defined here (rather than importing or
extending `app.breakouts.types.Direction`) to avoid any cross-package edit
conflicts with the breakout engine, which other engineers own in parallel —
and because patterns need a NEUTRAL case (e.g. a doji or a symmetric
triangle) that `Direction` doesn't carry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, TypedDict


class PatternDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Candle(TypedDict, total=False):
    open: str | float | Decimal
    high: str | float | Decimal
    low: str | float | Decimal
    close: str | float | Decimal
    volume: str | float | Decimal


@dataclass(frozen=True, slots=True)
class PatternMatch:
    """A single detected pattern, candlestick or structural."""

    name: str
    confidence: float  # 0-1
    direction: PatternDirection
    support: Decimal | None = None
    resistance: Decimal | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class PivotKind(str, Enum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Pivot:
    """A local high/low pivot detected on a rolling window of candles."""

    index: int
    price: Decimal
    kind: PivotKind
