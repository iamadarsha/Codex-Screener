"""Pure data types for the breakout engine — no logic, mirrors the role
`app.screener.dsl.ast` plays for the DSL package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class TriggerType(str, Enum):
    PDH_PDL = "pdh_pdl"
    ORB = "orb"
    FIFTY_TWO_WEEK = "52w"
    DONCHIAN = "donchian"
    NR4 = "nr4"
    NR7 = "nr7"
    INSIDE_BAR = "inside_bar"
    VOLUME_BREAKOUT = "volume_breakout"
    VWAP = "vwap"
    EMA_CROSS = "ema_cross"
    MACD_CROSS = "macd_cross"
    BOLLINGER_SQUEEZE = "bollinger_squeeze"


class BreakoutStatus(str, Enum):
    ARMED = "armed"  # level known, not yet crossed (or re-armed after a prior confirm reversed)
    TRIGGERED = "triggered"  # crossed this cycle; confirmation window open
    CONFIRMED = "confirmed"  # confirmation criteria satisfied — alertable
    INVALIDATED = "invalidated"  # reversed back through the level before confirming
    EXPIRED = "expired"  # confirmation window elapsed unconfirmed, or session-scoped level's day ended
    FAILED = "failed"  # reversed back through the level AFTER confirming — a false breakout


class RawEvent(str, Enum):
    NONE = "none"
    CROSS_UP = "cross_up"
    CROSS_DOWN = "cross_down"
    HOLD = "hold"
    REVERSE = "reverse"


class ExpiryPolicy(str, Enum):
    END_OF_DAY = "end_of_day"  # ORB, PDH/PDL, NR4/NR7, inside-bar, volume breakout, VWAP
    ROLLING_BARS = "rolling_bars"  # 52W, Donchian, EMA cross, MACD cross, Bollinger squeeze


@dataclass(frozen=True, slots=True)
class ReferenceLevel:
    trigger_type: TriggerType
    direction: Direction
    level: Decimal
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DetectorResult:
    level: ReferenceLevel
    event: RawEvent
    price: Decimal  # the value compared against level.level (price, or volume for volume_breakout)
    volume_ratio: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BreakoutSignal:
    """An emitted breakout lifecycle transition worth surfacing.

    Only produced by `BreakoutTracker.evaluate()` on CONFIRMED / INVALIDATED /
    EXPIRED / FAILED transitions — ARMED/TRIGGERED are internal tracker
    states, never turned into a `BreakoutSignal`. FAILED marks a breakout
    that reversed *after* confirming (distinct from INVALIDATED, which is a
    pre-confirmation reversal).
    """

    symbol: str
    trigger_type: TriggerType
    direction: Direction
    status: BreakoutStatus
    reference_level: Decimal
    trigger_price: Decimal
    confirmation_price: Decimal | None
    triggered_at: datetime
    confirmed_at: datetime | None
    bars_confirmed: int
    score: float | None = None
    volume_ratio: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)
