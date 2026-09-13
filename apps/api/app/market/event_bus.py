"""Typed realtime event model (master prompt §44).

Events publish to the existing Redis pub/sub channels rather than a new
transport — `/ws/prices` (app/ws/prices.py) already subscribes to
`price_updates`; this module is the single place that constructs event
payloads so every producer (nse_poller.py's fallback path and this
package's live path) agrees on the wire shape.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from app.services.redis_cache import publish

PRICE_UPDATES_CHANNEL = "price_updates"
CANDLE_UPDATES_CHANNEL = "candle_updates"
INDICATOR_UPDATES_CHANNEL = "indicator_updates"
MARKET_STATUS_CHANNEL = "market_status_updates"


class EventType(str, Enum):
    CANDLE_UPDATE = "candle_update"
    INDICATOR_UPDATE = "indicator_update"
    MARKET_STATUS = "market_status"


@dataclass(frozen=True, slots=True)
class PriceUpdateEvent:
    """Matches nse_poller.py's existing flat price_data shape exactly —
    both the fallback path and this package's live path publish the same
    wire format, and the frontend's PriceSocket (apps/web/src/lib/socket.ts)
    already parses this shape correctly. No envelope: standardizing on the
    flat shape that actually works today rather than the unused
    `{type:"price", data:{...}}` envelope the frontend optionally checked
    for (Phase 2 plan §C)."""

    symbol: str
    ltp: float
    open: float
    high: float
    low: float
    close: float
    prev_close: float
    change: float
    change_pct: float
    volume: int
    timestamp: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CandleUpdateEvent:
    symbol: str
    timeframe: str
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_payload(self) -> dict[str, Any]:
        return {"type": EventType.CANDLE_UPDATE.value, "data": asdict(self)}


@dataclass(frozen=True, slots=True)
class IndicatorUpdateEvent:
    symbol: str
    timeframe: str
    indicators: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "type": EventType.INDICATOR_UPDATE.value,
            "data": {"symbol": self.symbol, "timeframe": self.timeframe, "indicators": self.indicators},
        }


@dataclass(frozen=True, slots=True)
class MarketStatusEvent:
    segment: str
    status: str
    timestamp: str

    def to_payload(self) -> dict[str, Any]:
        return {"type": EventType.MARKET_STATUS.value, "data": asdict(self)}


async def publish_price_update(event: PriceUpdateEvent) -> None:
    await publish(PRICE_UPDATES_CHANNEL, json.dumps(event.to_payload()))


async def publish_candle_update(event: CandleUpdateEvent) -> None:
    await publish(CANDLE_UPDATES_CHANNEL, json.dumps(event.to_payload()))


async def publish_indicator_update(event: IndicatorUpdateEvent) -> None:
    await publish(INDICATOR_UPDATES_CHANNEL, json.dumps(event.to_payload()))


async def publish_market_status(event: MarketStatusEvent) -> None:
    await publish(MARKET_STATUS_CHANNEL, json.dumps(event.to_payload()))
