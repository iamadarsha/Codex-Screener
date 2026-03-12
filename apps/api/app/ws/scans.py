from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

CHANNEL = "scans"


@router.websocket("/ws/scans")
async def ws_scans(websocket: WebSocket):
    """
    WebSocket endpoint for scan result updates.

    Server pushes scan results when new breakouts are detected.
    Format: {"scan_id": "...", "scan_name": "...", "matches": [...], "run_at": "..."}
    """
    await manager.connect(websocket, CHANNEL)

    push_task: asyncio.Task | None = None

    async def _push_scan_results():
        """Listen to Redis pub/sub for scan result updates."""
        try:
            from app.services.redis_cache import get_redis

            redis = await get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe("scan_results")

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
            logger.exception("Scan push task error")

    push_task = asyncio.create_task(_push_scan_results())

    try:
        while True:
            # Keep connection alive; client may send ping/config
            msg = await websocket.receive_json()
            if msg.get("type") == "ping":
                await manager.send_to(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS scans error")
    finally:
        if push_task and not push_task.done():
            push_task.cancel()
        await manager.disconnect(websocket, CHANNEL)
