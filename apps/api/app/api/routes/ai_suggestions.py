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
        logger.info("background_generate: already running, skipping")
        return
    _generating = True
    try:
        from app.services.ai_suggestions import generate_suggestions
        logger.info("background_generate: starting 3-layer generation")
        result = await asyncio.wait_for(generate_suggestions(), timeout=90)
        total = sum(len(result.get(k, [])) for k in ("intraday", "weekly", "monthly"))
        logger.info("background_generate: done source=%s picks=%d", result.get("source", "?"), total)
    except asyncio.TimeoutError:
        logger.error("background_generate: global 90s timeout exceeded")
    except Exception as e:
        logger.error("background_generate_failed: %s %s", type(e).__name__, e, exc_info=True)
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

        result = await asyncio.wait_for(generate_suggestions(), timeout=80)
        return result
    except asyncio.TimeoutError:
        logger.error("refresh_ai_suggestions: 80s timeout exceeded")
        raise HTTPException(status_code=504, detail="Generation timed out. Picks will be generated in background on next visit.")
    except Exception as exc:
        logger.exception("Failed to refresh AI suggestions")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
