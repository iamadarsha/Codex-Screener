"""Upstox V3 WebSocket market data streamer."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Callable, Coroutine

import structlog
import websockets
import websockets.exceptions

from app.services.candle_builder import CandleBuilder
from app.services.redis_cache import get_redis, set_with_ttl
from app.services.upstox_auth import get_token
from app.services.upstox_instruments import get_symbol
from app.utils.redis_keys import (
    KEY_WS_LAST_TICK,
    TTL_LTP,
    TTL_WS_TICK,
    ltp_key,
    ltp_symbol_key,
)
from app.utils.time import now_ist

log = structlog.get_logger(__name__)

_WS_URL = "wss://api.upstox.com/v2/feed/market-data-feed"

# Silence detection: if no tick arrives within this window we reconnect
_SILENCE_SECONDS = 60

# Reconnect back-off limits
_RECONNECT_MIN_WAIT = 1.0
_RECONNECT_MAX_WAIT = 60.0


class UpstoxStreamer:
    """Manages a persistent WebSocket connection to Upstox market-data feed.

    Decoded ticks are forwarded to :class:`CandleBuilder` and cached as LTPs
    in Redis.
    """

    def __init__(self) -> None:
        self._ws: Any | None = None
        self._instruments: list[str] = []
        self._candle_builder = CandleBuilder()
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._on_candle: Callable[..., Coroutine[Any, Any, None]] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def connect(
        self,
        instruments: list[str],
        on_candle: Callable[..., Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        """Open the WebSocket and begin consuming ticks.

        Parameters
        ----------
        instruments:
            List of Upstox instrument keys to subscribe to.
        on_candle:
            Optional async callback invoked with each completed candle dict.
        """
        self._instruments = instruments
        self._on_candle = on_candle
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("streamer_started", instrument_count=len(instruments))

    async def disconnect(self) -> None:
        """Stop the streamer gracefully."""
        self._running = False
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        if self._task is not None:
            self._task.cancel()
            self._task = None
        log.info("streamer_stopped")

    async def subscribe(self, instrument_keys: list[str]) -> None:
        """Subscribe to additional instrument keys on the live connection."""
        self._instruments = list(set(self._instruments + instrument_keys))
        if self._ws is not None:
            await self._send_subscription("subscribe", instrument_keys)
            log.info("streamer_subscribed", keys=instrument_keys)

    async def unsubscribe(self, instrument_keys: list[str]) -> None:
        """Unsubscribe from instrument keys."""
        self._instruments = [k for k in self._instruments if k not in instrument_keys]
        if self._ws is not None:
            await self._send_subscription("unsubscribe", instrument_keys)
            log.info("streamer_unsubscribed", keys=instrument_keys)

    # ------------------------------------------------------------------
    # Connection loop with auto-reconnect
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        backoff = _RECONNECT_MIN_WAIT
        while self._running:
            try:
                await self._connect_and_consume()
                backoff = _RECONNECT_MIN_WAIT  # reset on clean disconnect
            except (
                websockets.exceptions.ConnectionClosed,
                websockets.exceptions.WebSocketException,
                OSError,
            ) as exc:
                log.warning("ws_disconnected", error=str(exc), backoff=backoff)
            except asyncio.CancelledError:
                break
            except Exception:
                log.exception("ws_unexpected_error")

            if self._running:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _RECONNECT_MAX_WAIT)

    async def _connect_and_consume(self) -> None:
        token = await get_token()
        if token is None:
            log.error("ws_no_token", hint="Upstox token missing; cannot connect")
            await asyncio.sleep(30)
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
        }

        async with websockets.connect(
            _WS_URL,
            additional_headers=headers,
            ping_interval=25,
            ping_timeout=10,
        ) as ws:
            self._ws = ws
            await self._send_subscription("subscribe", self._instruments)
            log.info("ws_connected", instruments=len(self._instruments))

            async for message in ws:
                await self._handle_message(message)

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def _handle_message(self, raw: bytes | str) -> None:
        """Decode and dispatch a single WebSocket message.

        Upstox V3 sends binary protobuf frames.  We attempt protobuf
        decoding first; if that fails we fall back to JSON (useful during
        development / testing).
        """
        tick_data = self._decode(raw)
        if tick_data is None:
            return

        ts = now_ist()
        await set_with_ttl(KEY_WS_LAST_TICK, ts.isoformat(), TTL_WS_TICK)

        feeds: dict[str, Any] = tick_data.get("feeds", {})
        for instrument_key, feed in feeds.items():
            ltpc = feed.get("ff", {}).get("marketFF", {}).get("ltpc", {})
            ltp_val = ltpc.get("ltp")
            if ltp_val is None:
                continue

            # Cache LTP
            r = await get_redis()
            await r.set(ltp_key(instrument_key), str(ltp_val), ex=TTL_LTP)

            symbol = await get_symbol(instrument_key)
            if symbol:
                await r.set(ltp_symbol_key(symbol), str(ltp_val), ex=TTL_LTP)

                # Feed into candle builder
                volume = int(ltpc.get("vol", 0))
                completed = await self._candle_builder.on_tick(
                    symbol=symbol,
                    ltp=float(ltp_val),
                    volume=volume,
                    ts=ts,
                )
                if completed and self._on_candle:
                    for candle in completed:
                        try:
                            await self._on_candle(candle)
                        except Exception:
                            log.exception("on_candle_callback_error", candle=candle)

    @staticmethod
    def _decode(raw: bytes | str) -> dict[str, Any] | None:
        """Best-effort decode of a WebSocket frame.

        Tries protobuf first, then JSON.
        """
        # Try protobuf decoding
        if isinstance(raw, bytes):
            try:
                from google.protobuf.json_format import MessageToDict

                from MarketDataFeed_pb2 import FeedResponse  # type: ignore[import-untyped]

                msg = FeedResponse()
                msg.ParseFromString(raw)
                return MessageToDict(msg)
            except Exception:
                pass

            # Fallback: maybe it is gzipped JSON
            try:
                import gzip

                decompressed = gzip.decompress(raw)
                return json.loads(decompressed)
            except Exception:
                pass

        # Plain JSON string
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass

        log.debug("ws_decode_failed", size=len(raw) if isinstance(raw, bytes) else len(str(raw)))
        return None

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    async def _send_subscription(self, action: str, instrument_keys: list[str]) -> None:
        if self._ws is None or not instrument_keys:
            return
        payload = json.dumps(
            {
                "guid": f"bos-{int(time.time())}",
                "method": action,
                "data": {
                    "mode": "full",
                    "instrumentKeys": instrument_keys,
                },
            }
        )
        await self._ws.send(payload)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @staticmethod
    async def is_feed_alive() -> bool:
        """Return ``True`` if the last tick arrived within the silence window."""
        r = await get_redis()
        last = await r.get(KEY_WS_LAST_TICK)
        if last is None:
            return False
        from datetime import datetime

        last_dt = datetime.fromisoformat(last)
        return (now_ist() - last_dt).total_seconds() < _SILENCE_SECONDS
