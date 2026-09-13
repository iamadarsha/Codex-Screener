"""Memory-first per-symbol market state.

Bounded ring buffers keep recent ticks/candles in-process, avoiding a
database or Redis round-trip on every tick for the hot path. Redis remains
the durable current-candle store (see candles.py) — this is purely an
in-process speed/reference layer sitting in front of it, per master prompt
§20 ("memory-first state... bounded ring buffers").
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from app.market.normalize import Tick

_DEFAULT_TICK_BUFFER = 200
_DEFAULT_CANDLE_BUFFER = 300


@dataclass
class SymbolState:
    symbol: str
    recent_ticks: deque[Tick] = field(default_factory=lambda: deque(maxlen=_DEFAULT_TICK_BUFFER))
    recent_candles: dict[str, deque[dict]] = field(default_factory=dict)
    latest_tick: Tick | None = None
    last_tick_at: datetime | None = None
    cumulative_day_volume: int | None = None  # sourced from `vtt`, when present

    def record_tick(self, tick: Tick) -> None:
        self.recent_ticks.append(tick)
        self.latest_tick = tick
        self.last_tick_at = tick.received_at
        if tick.vtt is not None:
            self.cumulative_day_volume = tick.vtt

    def record_candle(self, timeframe: str, candle: dict) -> None:
        buf = self.recent_candles.setdefault(timeframe, deque(maxlen=_DEFAULT_CANDLE_BUFFER))
        buf.append(candle)

    def candles(self, timeframe: str) -> list[dict]:
        return list(self.recent_candles.get(timeframe, ()))

    def is_stale(self, now: datetime, threshold_seconds: float) -> bool:
        if self.last_tick_at is None:
            return True
        return (now - self.last_tick_at).total_seconds() > threshold_seconds


class MarketState:
    """Registry of :class:`SymbolState`, keyed by symbol."""

    def __init__(self) -> None:
        self._symbols: dict[str, SymbolState] = {}

    def get_or_create(self, symbol: str) -> SymbolState:
        state = self._symbols.get(symbol)
        if state is None:
            state = SymbolState(symbol=symbol)
            self._symbols[symbol] = state
        return state

    def get(self, symbol: str) -> SymbolState | None:
        return self._symbols.get(symbol)

    def all_symbols(self) -> list[str]:
        return list(self._symbols.keys())

    def stale_symbols(self, now: datetime, threshold_seconds: float) -> list[str]:
        return [s for s, state in self._symbols.items() if state.is_stale(now, threshold_seconds)]
