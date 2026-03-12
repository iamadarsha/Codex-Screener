from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, status
from upstox_client.feeder.market_data_streamer_v3 import MarketDataStreamerV3

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from data.candle_builder import Candle, TickEvent, get_candle_builder
from data.indicator_engine import get_indicator_engine
from data.upstox_auth import UpstoxAuthError, build_api_client, get_access_token, validate_token
from data.upstox_instruments import (
    InstrumentSyncError,
    SYMBOL_TO_KEY_HASH,
    UNIVERSE_NIFTY500_KEY,
    get_key_to_symbol_map,
    get_symbol_to_key_map,
    get_universe_members,
    sync_instruments_to_redis,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/data/streamer", tags=["upstox-streamer"])

STREAMER_STATUS_KEY = "streamer:status"
STREAMER_MARKET_INFO_KEY = "streamer:market_info"
LAST_TICK_KEY = "streamer:last_tick_at"

FULL_MODE_LIMIT = 1500
LTPC_MODE_LIMIT = 3000

_redis_client: redis.Redis[str] | None = None


class UpstoxStreamerError(BreakoutScanError):
    """Raised when the live streamer cannot start or process ticks."""


@dataclass(slots=True)
class SubscriptionBatch:
    name: str
    mode: str
    instrument_keys: list[str]


@dataclass(slots=True)
class ConnectionState:
    batch: SubscriptionBatch
    streamer: MarketDataStreamerV3 | None
    connected: bool
    reconnect_attempts: int
    last_error: str | None
    last_opened_at: str | None
    last_closed_at: str | None

    def to_status(self) -> dict[str, object]:
        return {
            "name": self.batch.name,
            "mode": self.batch.mode,
            "instrument_count": len(self.batch.instrument_keys),
            "connected": self.connected,
            "reconnect_attempts": self.reconnect_attempts,
            "last_error": self.last_error,
            "last_opened_at": self.last_opened_at,
            "last_closed_at": self.last_closed_at,
        }


def get_redis_client() -> redis.Redis[str]:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def decimal_from_value(value: object) -> Decimal | None:
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def datetime_from_epoch_ms(value: object, fallback_ms: object) -> datetime:
    candidate = value if value not in (None, "") else fallback_ms
    if candidate in (None, ""):
        return datetime.now(tz=UTC)

    timestamp_ms = int(str(candidate))
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)


class UpstoxStreamerManager:
    def __init__(self) -> None:
        self.redis = get_redis_client()
        self.candle_builder = get_candle_builder()
        self.candle_builder.on_candle_close = self.handle_candle_close
        self.indicator_engine = get_indicator_engine()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.running = False
        self.tick_count = 0
        self.last_tick_at: datetime | None = None
        self.market_info: dict[str, str] = {}
        self.instrument_lookup: dict[str, str] = {}
        self.last_traded_totals: dict[str, int] = {}
        self.connections: dict[str, ConnectionState] = {}
        self.reconnect_tasks: dict[str, asyncio.Task[None]] = {}

    async def start(self) -> dict[str, object]:
        if self.running:
            return await self.status()

        try:
            self.loop = asyncio.get_running_loop()
            self.tick_count = 0
            self.last_tick_at = None
            self.market_info = {}
            self.connections.clear()
            self.last_traded_totals.clear()
            self.candle_builder.reset()
            access_token = await get_access_token(required=True)
            await validate_token(access_token)
            await self._ensure_instruments()
            batches = await self._build_batches()
            if not batches:
                raise UpstoxStreamerError("No subscription batches were built from instrument maps.")

            self.running = True
            for batch in batches:
                await self._connect_batch(batch, access_token)
            await self._cache_status()
        except (UpstoxAuthError, InstrumentSyncError, UpstoxStreamerError):
            raise
        except Exception as error:
            self.running = False
            raise UpstoxStreamerError("Unexpected error while starting the Upstox streamer.") from error

        return await self.status()

    async def stop(self) -> dict[str, object]:
        self.running = False

        for task in self.reconnect_tasks.values():
            task.cancel()
        self.reconnect_tasks.clear()

        for state in self.connections.values():
            if state.streamer is not None:
                try:
                    await asyncio.to_thread(state.streamer.disconnect)
                except Exception:
                    logger.warning("failed to disconnect streamer batch %s", state.batch.name)
            state.connected = False
            state.last_closed_at = datetime.now(tz=UTC).isoformat()

        await self._cache_status()
        return await self.status()

    async def status(self) -> dict[str, object]:
        return {
            "running": self.running,
            "tick_count": self.tick_count,
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at is not None else None,
            "quote_mode_normalized_to": "full",
            "connections": [state.to_status() for state in self.connections.values()],
            "market_info": self.market_info,
        }

    async def _ensure_instruments(self) -> None:
        instrument_map = await get_symbol_to_key_map()
        if instrument_map:
            return
        await sync_instruments_to_redis()

    async def _build_batches(self) -> list[SubscriptionBatch]:
        symbol_map = await get_symbol_to_key_map()
        reverse_map = await get_key_to_symbol_map()
        self.instrument_lookup = reverse_map

        if not symbol_map:
            raise UpstoxStreamerError("Instrument maps are empty. Run the instrument sync first.")

        nifty500_symbols = await get_universe_members(UNIVERSE_NIFTY500_KEY)
        nifty500_symbol_set = set(nifty500_symbols)

        full_keys = [symbol_map[symbol] for symbol in nifty500_symbols if symbol in symbol_map]
        ltpc_keys = [
            instrument_key
            for symbol, instrument_key in symbol_map.items()
            if symbol not in nifty500_symbol_set
        ]

        batches: list[SubscriptionBatch] = []
        for index, instrument_keys in enumerate(chunked(full_keys, FULL_MODE_LIMIT), start=1):
            batches.append(
                SubscriptionBatch(
                    name=f"full-{index}",
                    mode=MarketDataStreamerV3.Mode["FULL"],
                    instrument_keys=instrument_keys,
                )
            )

        for index, instrument_keys in enumerate(chunked(ltpc_keys, LTPC_MODE_LIMIT), start=1):
            batches.append(
                SubscriptionBatch(
                    name=f"ltpc-{index}",
                    mode=MarketDataStreamerV3.Mode["LTPC"],
                    instrument_keys=instrument_keys,
                )
            )

        return batches

    async def _connect_batch(self, batch: SubscriptionBatch, access_token: str) -> None:
        state = ConnectionState(
            batch=batch,
            streamer=None,
            connected=False,
            reconnect_attempts=0,
            last_error=None,
            last_opened_at=None,
            last_closed_at=None,
        )
        self.connections[batch.name] = state
        state.streamer = self._create_streamer(batch, access_token)
        state.streamer.connect()

    def _create_streamer(self, batch: SubscriptionBatch, access_token: str) -> MarketDataStreamerV3:
        api_client = build_api_client(access_token)
        streamer = MarketDataStreamerV3(
            api_client=api_client,
            instrumentKeys=batch.instrument_keys,
            mode=batch.mode,
        )
        streamer.auto_reconnect(False)
        streamer.on(streamer.Event["OPEN"], lambda: self._schedule(self._on_open(batch.name)))
        streamer.on(
            streamer.Event["CLOSE"],
            lambda close_status_code, close_msg: self._schedule(
                self._on_close(batch.name, close_status_code, close_msg)
            ),
        )
        streamer.on(
            streamer.Event["ERROR"],
            lambda error: self._schedule(self._on_error(batch.name, str(error))),
        )
        streamer.on(
            streamer.Event["MESSAGE"],
            lambda message: self._schedule(
                self._on_message(batch.name, cast(dict[str, object], message))
            ),
        )
        return streamer

    def _schedule(self, coroutine: Coroutine[object, object, object]) -> None:
        if self.loop is None:
            return

        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        future.add_done_callback(self._log_future_exception)

    @staticmethod
    def _log_future_exception(future: object) -> None:
        try:
            if hasattr(future, "result"):
                getattr(future, "result")()
        except Exception:
            logger.exception("streamer callback failed")

    async def _on_open(self, batch_name: str) -> None:
        state = self.connections[batch_name]
        state.connected = True
        state.last_opened_at = datetime.now(tz=UTC).isoformat()
        state.last_error = None
        await self._cache_status()

    async def _on_close(self, batch_name: str, close_status_code: int, close_msg: str | None) -> None:
        state = self.connections[batch_name]
        state.connected = False
        state.last_closed_at = datetime.now(tz=UTC).isoformat()
        if self.running:
            await self._schedule_reconnect(batch_name, f"closed:{close_status_code}:{close_msg or ''}")
        await self._cache_status()

    async def _on_error(self, batch_name: str, error: str) -> None:
        state = self.connections[batch_name]
        state.connected = False
        state.last_error = error
        if self.running and "401 Unauthorized" not in error:
            await self._schedule_reconnect(batch_name, error)
        await self._cache_status()

    async def _schedule_reconnect(self, batch_name: str, reason: str) -> None:
        if batch_name in self.reconnect_tasks:
            return

        state = self.connections[batch_name]
        state.reconnect_attempts += 1
        state.last_error = reason
        delay = min(2 ** max(state.reconnect_attempts - 1, 0), 30)

        async def reconnect() -> None:
            try:
                await asyncio.sleep(delay)
                if not self.running:
                    return
                access_token = await get_access_token(required=True)
                state.streamer = self._create_streamer(state.batch, access_token)
                state.streamer.connect()
            except Exception:
                logger.exception("streamer reconnect failed for %s", batch_name)
            finally:
                self.reconnect_tasks.pop(batch_name, None)
                await self._cache_status()

        self.reconnect_tasks[batch_name] = asyncio.create_task(reconnect())
        await self._cache_status()

    async def _on_message(self, batch_name: str, message: dict[str, object]) -> None:
        try:
            message_type = str(message.get("type", ""))
            current_ts = message.get("currentTs")

            if message_type == "market_info":
                market_info = cast(dict[str, object], message.get("marketInfo", {}))
                segment_status = cast(dict[str, str], market_info.get("segmentStatus", {}))
                self.market_info = segment_status
                await self.redis.hset(STREAMER_MARKET_INFO_KEY, mapping=segment_status)
                await self.redis.expire(STREAMER_MARKET_INFO_KEY, settings.redis_short_ttl_seconds)
                await self._cache_status()
                return

            if message_type != "live_feed":
                return

            feeds = cast(dict[str, dict[str, object]], message.get("feeds", {}))
            for instrument_key, feed in feeds.items():
                tick = self._extract_tick(instrument_key, feed, current_ts)
                if tick is None:
                    continue
                await self._handle_tick(tick)
        except UpstoxStreamerError:
            raise
        except Exception as error:
            raise UpstoxStreamerError(
                f"Unable to process live feed message from batch {batch_name}."
            ) from error

    def _extract_tick(
        self,
        instrument_key: str,
        feed: dict[str, object],
        current_ts: object,
    ) -> TickEvent | None:
        ltpc_block = cast(dict[str, object] | None, feed.get("ltpc"))
        full_feed = cast(dict[str, object], feed.get("fullFeed", {}))
        first_level = cast(dict[str, object], feed.get("firstLevelWithGreeks", {}))
        market_ff = cast(dict[str, object], full_feed.get("marketFF", {}))

        if ltpc_block is None:
            if "ltpc" in market_ff:
                ltpc_block = cast(dict[str, object], market_ff.get("ltpc"))
            elif "ltpc" in first_level:
                ltpc_block = cast(dict[str, object], first_level.get("ltpc"))

        if ltpc_block is None:
            return None

        price = decimal_from_value(ltpc_block.get("ltp"))
        previous_close = decimal_from_value(ltpc_block.get("cp"))
        timestamp = datetime_from_epoch_ms(ltpc_block.get("ltt"), current_ts)
        last_traded_quantity = int(str(ltpc_block.get("ltq", "0")))
        total_volume = market_ff.get("vtt", first_level.get("vtt"))
        parsed_total_volume = int(str(total_volume)) if total_volume not in (None, "") else None

        if price is None:
            return None

        if parsed_total_volume is not None:
            previous_total = self.last_traded_totals.get(instrument_key)
            if previous_total is not None:
                last_traded_quantity = max(parsed_total_volume - previous_total, 0)
            self.last_traded_totals[instrument_key] = parsed_total_volume

        symbol = self.instrument_lookup.get(instrument_key, instrument_key)
        return TickEvent(
            symbol=symbol,
            instrument_key=instrument_key,
            price=price,
            timestamp=timestamp,
            quantity=last_traded_quantity,
            total_volume=parsed_total_volume,
            previous_close=previous_close,
        )

    async def _handle_tick(self, tick: TickEvent) -> None:
        self.tick_count += 1
        self.last_tick_at = tick.timestamp
        payload = {
            "symbol": tick.symbol,
            "instrument_key": tick.instrument_key,
            "price": str(tick.price),
            "timestamp": tick.timestamp.isoformat(),
            "quantity": tick.quantity,
            "total_volume": tick.total_volume,
            "previous_close": str(tick.previous_close) if tick.previous_close is not None else None,
        }

        try:
            pipeline = self.redis.pipeline()
            pipeline.set(
                f"ltp:{tick.instrument_key}",
                json.dumps(payload),
                ex=settings.redis_short_ttl_seconds,
            )
            pipeline.set(
                LAST_TICK_KEY,
                tick.timestamp.isoformat(),
                ex=settings.redis_short_ttl_seconds,
            )
            pipeline.publish("ticks", json.dumps(payload))
            await pipeline.execute()
        except redis.RedisError as error:
            raise UpstoxStreamerError(f"Unable to publish tick data for {tick.symbol}.") from error

        await self.candle_builder.ingest_tick(tick)
        await self._cache_status()

    async def handle_candle_close(self, candle: Candle) -> None:
        candles = self.candle_builder.get_buffer(candle.symbol, candle.timeframe)
        if not candles:
            return

        try:
            snapshot = await self.indicator_engine.compute_and_store(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                candles=candles,
            )
            await self.redis.set(
                f"candle:{candle.symbol}:{candle.timeframe}:latest",
                json.dumps(candle.to_json()),
                ex=settings.redis_indicator_ttl_seconds,
            )
            await self.redis.expire(
                f"ind:{snapshot.symbol}:{snapshot.timeframe}",
                settings.redis_indicator_ttl_seconds,
            )
        except Exception as error:
            raise UpstoxStreamerError(
                f"Unable to finalize indicators for {candle.symbol} {candle.timeframe}."
            ) from error

    async def _cache_status(self) -> None:
        mapping = {
            "running": str(self.running).lower(),
            "tick_count": str(self.tick_count),
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at is not None else "",
            "connection_count": str(len(self.connections)),
            "instrument_cache_key": SYMBOL_TO_KEY_HASH,
        }
        try:
            await self.redis.hset(STREAMER_STATUS_KEY, mapping=mapping)
            await self.redis.expire(STREAMER_STATUS_KEY, settings.redis_short_ttl_seconds)
        except redis.RedisError as error:
            raise UpstoxStreamerError("Unable to cache the streamer status in Redis.") from error


_manager: UpstoxStreamerManager | None = None


def get_streamer_manager() -> UpstoxStreamerManager:
    global _manager

    if _manager is None:
        _manager = UpstoxStreamerManager()

    return _manager


@router.post("/start")
async def start_streamer() -> dict[str, object]:
    manager = get_streamer_manager()
    try:
        return await manager.start()
    except (UpstoxAuthError, InstrumentSyncError, UpstoxStreamerError) as error:
        logger.exception("streamer start failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/stop")
async def stop_streamer() -> dict[str, object]:
    manager = get_streamer_manager()
    try:
        return await manager.stop()
    except UpstoxStreamerError as error:
        logger.exception("streamer stop failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/status")
async def streamer_status() -> dict[str, object]:
    manager = get_streamer_manager()
    try:
        return await manager.status()
    except UpstoxStreamerError as error:
        logger.exception("streamer status failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
