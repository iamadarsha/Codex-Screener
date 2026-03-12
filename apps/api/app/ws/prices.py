from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

CHANNEL = "prices"


@router.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    """
    WebSocket endpoint for live price updates.

    Client sends: {"subscribe": ["RELIANCE", "TCS", ...]}
    Server sends: {"symbol": "RELIANCE", "ltp": 2450.5, "change_pct": 1.2, ...}
    """
    await manager.connect(websocket, CHANNEL)
    subscribed_symbols: set[str] = set()

    # Background task to push price updates from Redis pub/sub
    push_task: asyncio.Task | None = None

    async def _push_prices():
        """Listen to Redis pub/sub and forward matching updates."""
        try:
            from app.services.redis_cache import get_redis

            redis = await get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe("price_updates")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    import json

                    data = json.loads(message["data"])
                    symbol = data.get("symbol", "")
                    if not subscribed_symbols or symbol in subscribed_symbols:
                        await manager.send_to(websocket, data)
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Price push task error")

    try:
        while True:
            msg = await websocket.receive_json()

            if "subscribe" in msg:
                symbols = msg["subscribe"]
                if isinstance(symbols, list):
                    subscribed_symbols = {s.upper() for s in symbols}
                    await manager.send_to(
                        websocket,
                        {"type": "subscribed", "symbols": sorted(subscribed_symbols)},
                    )

                    # Start push task if not already running
                    if push_task is None or push_task.done():
                        push_task = asyncio.create_task(_push_prices())

            elif "unsubscribe" in msg:
                symbols = msg["unsubscribe"]
                if isinstance(symbols, list):
                    subscribed_symbols -= {s.upper() for s in symbols}

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS prices error")
    finally:
        if push_task and not push_task.done():
            push_task.cancel()
        await manager.disconnect(websocket, CHANNEL)
