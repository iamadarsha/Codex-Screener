from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.utils.time import now_ist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-suggestions", tags=["ai-suggestions"])

# Track if a background generation is already running
_generating = False


async def _background_generate():
    """Run generation in background so the endpoint returns immediately."""
    global _generating
    if _generating:
        return
    _generating = True
    try:
        from app.services.ai_suggestions import generate_suggestions
        await generate_suggestions()
    except Exception as e:
        logger.error("background_generate_failed: %s", e)
    finally:
        _generating = False


@router.get("")
async def get_ai_suggestions(background_tasks: BackgroundTasks):
    """Return cached AI suggestions instantly. Triggers background generation if no cache."""
    try:
        from app.services.ai_suggestions import get_suggestions

        cached = await get_suggestions()
        if cached:
            return cached

        # No cache — trigger background generation and return empty immediately
        background_tasks.add_task(_background_generate)
        return {
            "intraday": [], "weekly": [], "monthly": [],
            "generated_at": now_ist().isoformat(),
            "headline_count": 0,
            "source": "pending",
            "message": "Generating AI picks in background. Refresh in ~30 seconds.",
        }
    except Exception as exc:
        logger.exception("Failed to get AI suggestions")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/refresh")
async def refresh_ai_suggestions():
    """Force regenerate AI stock suggestions (may take 10-60s)."""
    try:
        from app.services.ai_suggestions import generate_suggestions

        result = await generate_suggestions()
        return result
    except Exception as exc:
        logger.exception("Failed to refresh AI suggestions")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
