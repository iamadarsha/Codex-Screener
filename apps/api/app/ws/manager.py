from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections organized by channel."""

    def __init__(self) -> None:
        # channel -> set of websockets
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[channel].add(websocket)
        logger.info("WS connected to channel=%s (total=%d)", channel, len(self._connections[channel]))

    async def disconnect(self, websocket: WebSocket, channel: str | None = None) -> None:
        async with self._lock:
            if channel:
                self._connections[channel].discard(websocket)
            else:
                for ch in self._connections:
                    self._connections[ch].discard(websocket)
        logger.info("WS disconnected from channel=%s", channel or "all")

    async def broadcast(self, channel: str, data: dict) -> None:
        """Send data to all connections on a channel."""
        async with self._lock:
            dead: list[WebSocket] = []
            for ws in self._connections[channel]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._connections[channel].discard(ws)

    async def send_to(self, websocket: WebSocket, data: dict) -> None:
        """Send data to a specific connection."""
        try:
            await websocket.send_json(data)
        except Exception:
            logger.exception("Failed to send to websocket")

    @property
    def active_connections(self) -> dict[str, int]:
        return {ch: len(conns) for ch, conns in self._connections.items() if conns}


# Singleton manager instance
manager = ConnectionManager()
