from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

CHANNEL = "alerts"


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert triggers.

    Server pushes alert notifications when conditions are met.
    Format: {"alert_id": "...", "symbol": "...", "trigger_price": ..., "conditions_met": [...]}
    """
    await manager.connect(websocket, CHANNEL)

    push_task: asyncio.Task | None = None

    async def _push_alert_triggers():
        """Listen to Redis pub/sub for alert trigger events."""
        try:
            from app.services.redis_cache import get_redis

            redis = await get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe("alert_triggers")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    import json

                    data = json.loads(message["data"])
                    await manager.send_to(websocket, data)
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Alert push task error")

    push_task = asyncio.create_task(_push_alert_triggers())

    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "ping":
                await manager.send_to(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS alerts error")
    finally:
        if push_task and not push_task.done():
            push_task.cancel()
        await manager.disconnect(websocket, CHANNEL)
