from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.errors import BreakoutScanError

settings = get_settings()

TF_1MIN = "1min"
TF_5MIN = "5min"
TF_15MIN = "15min"
TF_30MIN = "30min"
TF_1HR = "1hr"

TIMEFRAME_MAXLEN: dict[str, int] = {
    TF_1MIN: 390,
    TF_5MIN: 200,
    TF_15MIN: 100,
    TF_30MIN: 80,
    TF_1HR: 50,
}

TIMEFRAME_TO_MINUTES: dict[str, int] = {
    TF_5MIN: 5,
    TF_15MIN: 15,
    TF_30MIN: 30,
    TF_1HR: 60,
}

MARKET_OPEN = time(9, 15)


class CandleBuilderError(BreakoutScanError):
    """Raised when the candle builder cannot process ticks."""


@dataclass(slots=True)
class TickEvent:
    symbol: str
    instrument_key: str
    price: Decimal
    timestamp: datetime
    quantity: int
    total_volume: int | None
    previous_close: Decimal | None = None


@dataclass(slots=True)
class Candle:
    symbol: str
    timeframe: str
    start_ts: datetime
    end_ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def to_json(self) -> dict[str, str | int]:
        payload = asdict(self)
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_ts": self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat(),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": self.volume,
        }


@dataclass(slots=True)
class CandleCloseEvent:
    symbol: str
    timeframe: str
    candle: Candle

    def to_json(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "candle": self.candle.to_json(),
        }


CandleCloseCallback = Callable[[Candle], Awaitable[None]]


def minute_floor(timestamp: datetime) -> datetime:
    return timestamp.astimezone(UTC).replace(second=0, microsecond=0)


def market_bucket_start(timestamp: datetime, timeframe_minutes: int) -> datetime:
    market_tz = ZoneInfo(settings.market_timezone)
    local_timestamp = timestamp.astimezone(market_tz)
    session_open = datetime.combine(local_timestamp.date(), MARKET_OPEN, tzinfo=market_tz)
    local_floor = local_timestamp.replace(second=0, microsecond=0)

    if local_floor < session_open:
        bucket_minutes = local_floor.minute - (local_floor.minute % timeframe_minutes)
        aligned = local_floor.replace(minute=bucket_minutes)
        return aligned.astimezone(UTC)

    elapsed_minutes = int((local_floor - session_open).total_seconds() // 60)
    bucket_index = elapsed_minutes // timeframe_minutes
    bucket_start = session_open + timedelta(minutes=bucket_index * timeframe_minutes)
    return bucket_start.astimezone(UTC)


class CandleBuilder:
    def __init__(
        self,
        on_candle_close: CandleCloseCallback | None = None,
    ) -> None:
        self.on_candle_close = on_candle_close
        self.active_1min: dict[str, Candle] = {}
        self.partial_rollups: dict[str, dict[str, Candle]] = {
            timeframe: {}
            for timeframe in TIMEFRAME_TO_MINUTES
        }
        self.buffers: dict[str, dict[str, deque[Candle]]] = defaultdict(
            lambda: {
                timeframe: deque(maxlen=max_length)
                for timeframe, max_length in TIMEFRAME_MAXLEN.items()
            }
        )

    async def ingest_tick(self, tick: TickEvent) -> list[CandleCloseEvent]:
        try:
            return await self._ingest_tick(tick)
        except CandleBuilderError:
            raise
        except Exception as error:
            raise CandleBuilderError(f"Unable to process tick for {tick.symbol}.") from error

    async def _ingest_tick(self, tick: TickEvent) -> list[CandleCloseEvent]:
        events: list[CandleCloseEvent] = []
        minute_start = minute_floor(tick.timestamp)
        current = self.active_1min.get(tick.symbol)

        if current is None:
            self.active_1min[tick.symbol] = self._create_candle_from_tick(
                tick=tick,
                timeframe=TF_1MIN,
                start_ts=minute_start,
                end_ts=minute_start + timedelta(minutes=1),
            )
            return events

        if current.start_ts != minute_start:
            events.extend(await self._finalize_candle(current))
            self.active_1min[tick.symbol] = self._create_candle_from_tick(
                tick=tick,
                timeframe=TF_1MIN,
                start_ts=minute_start,
                end_ts=minute_start + timedelta(minutes=1),
            )
            return events

        self._update_candle(current, tick)
        return events

    async def flush_symbol(self, symbol: str) -> list[CandleCloseEvent]:
        try:
            events: list[CandleCloseEvent] = []
            current = self.active_1min.pop(symbol, None)
            if current is not None:
                events.extend(await self._finalize_candle(current))

            for timeframe in TIMEFRAME_TO_MINUTES:
                partial = self.partial_rollups[timeframe].pop(symbol, None)
                if partial is not None:
                    events.extend(await self._append_closed_candle(partial))

            return events
        except Exception as error:
            raise CandleBuilderError(f"Unable to flush candle state for {symbol}.") from error

    async def _finalize_candle(self, candle: Candle) -> list[CandleCloseEvent]:
        events = await self._append_closed_candle(candle)

        for timeframe, timeframe_minutes in TIMEFRAME_TO_MINUTES.items():
            rollup_event = await self._rollup_closed_minute(
                source_candle=candle,
                timeframe=timeframe,
                timeframe_minutes=timeframe_minutes,
            )
            events.extend(rollup_event)

        return events

    async def _rollup_closed_minute(
        self,
        source_candle: Candle,
        timeframe: str,
        timeframe_minutes: int,
    ) -> list[CandleCloseEvent]:
        bucket_start = market_bucket_start(source_candle.start_ts, timeframe_minutes)
        bucket_end = bucket_start + timedelta(minutes=timeframe_minutes)
        symbol = source_candle.symbol
        existing = self.partial_rollups[timeframe].get(symbol)

        if existing is None:
            self.partial_rollups[timeframe][symbol] = Candle(
                symbol=symbol,
                timeframe=timeframe,
                start_ts=bucket_start,
                end_ts=bucket_end,
                open=source_candle.open,
                high=source_candle.high,
                low=source_candle.low,
                close=source_candle.close,
                volume=source_candle.volume,
            )
            return []

        if existing.start_ts != bucket_start:
            events = await self._append_closed_candle(existing)
            self.partial_rollups[timeframe][symbol] = Candle(
                symbol=symbol,
                timeframe=timeframe,
                start_ts=bucket_start,
                end_ts=bucket_end,
                open=source_candle.open,
                high=source_candle.high,
                low=source_candle.low,
                close=source_candle.close,
                volume=source_candle.volume,
            )
            return events

        existing.high = max(existing.high, source_candle.high)
        existing.low = min(existing.low, source_candle.low)
        existing.close = source_candle.close
        existing.volume += source_candle.volume
        existing.end_ts = bucket_end
        return []

    async def _append_closed_candle(self, candle: Candle) -> list[CandleCloseEvent]:
        self.buffers[candle.symbol][candle.timeframe].append(candle)
        event = CandleCloseEvent(symbol=candle.symbol, timeframe=candle.timeframe, candle=candle)

        if self.on_candle_close is not None:
            await self.on_candle_close(candle)

        return [event]

    def get_buffer(self, symbol: str, timeframe: str) -> list[Candle]:
        if timeframe not in TIMEFRAME_MAXLEN:
            raise CandleBuilderError(f"Unsupported timeframe requested: {timeframe}.")

        return list(self.buffers[symbol][timeframe])

    def reset(self) -> None:
        self.active_1min.clear()
        for rollup_map in self.partial_rollups.values():
            rollup_map.clear()
        self.buffers.clear()

    @staticmethod
    def _create_candle_from_tick(
        tick: TickEvent,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> Candle:
        volume = tick.quantity
        if volume < 0:
            raise CandleBuilderError("Tick quantity cannot be negative.")

        return Candle(
            symbol=tick.symbol,
            timeframe=timeframe,
            start_ts=start_ts,
            end_ts=end_ts,
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=volume,
        )

    @staticmethod
    def _update_candle(candle: Candle, tick: TickEvent) -> None:
        candle.high = max(candle.high, tick.price)
        candle.low = min(candle.low, tick.price)
        candle.close = tick.price
        candle.volume += tick.quantity


_builder: CandleBuilder | None = None


def get_candle_builder() -> CandleBuilder:
    global _builder

    if _builder is None:
        _builder = CandleBuilder()

    return _builder


def build_validation_ticks(symbol: str = "RELIANCE") -> list[TickEvent]:
    start = datetime(2026, 3, 12, 9, 15, tzinfo=ZoneInfo(settings.market_timezone)).astimezone(UTC)
    ticks: list[TickEvent] = []

    for minute_offset in range(15):
        base_price = Decimal("100.00") + Decimal(minute_offset) / Decimal("10")
        for second_offset, adjustment in ((0, Decimal("0.00")), (20, Decimal("0.20")), (40, Decimal("-0.10"))):
            ticks.append(
                TickEvent(
                    symbol=symbol,
                    instrument_key=f"NSE_EQ|{symbol}",
                    price=base_price + adjustment,
                    timestamp=start + timedelta(minutes=minute_offset, seconds=second_offset),
                    quantity=100 + minute_offset,
                    total_volume=None,
                    previous_close=Decimal("99.50"),
                )
            )

    return ticks


async def validate_candle_builder() -> dict[str, object]:
    builder = CandleBuilder()
    ticks = build_validation_ticks()

    for tick in ticks:
        await builder.ingest_tick(tick)

    events = await builder.flush_symbol("RELIANCE")
    one_minute = builder.get_buffer("RELIANCE", TF_1MIN)
    five_minute = builder.get_buffer("RELIANCE", TF_5MIN)
    fifteen_minute = builder.get_buffer("RELIANCE", TF_15MIN)

    return {
        "closed_events": len(events),
        "one_minute_count": len(one_minute),
        "five_minute_count": len(five_minute),
        "fifteen_minute_count": len(fifteen_minute),
        "last_1min_close": str(one_minute[-1].close),
        "last_5min_volume": five_minute[-1].volume,
        "last_15min_high": str(fifteen_minute[-1].high),
    }
