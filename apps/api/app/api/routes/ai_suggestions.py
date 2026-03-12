from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-suggestions", tags=["ai-suggestions"])


@router.get("")
async def get_ai_suggestions():
    """Return cached AI stock suggestions or generate fresh ones."""
    try:
        from app.services.ai_suggestions import generate_suggestions, get_suggestions

        cached = await get_suggestions()
        if cached:
            return cached

        result = await generate_suggestions()
        return result
    except Exception as exc:
        logger.exception("Failed to get AI suggestions")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/refresh")
async def refresh_ai_suggestions():
    """Force regenerate AI stock suggestions."""
    try:
        from app.services.ai_suggestions import generate_suggestions

        result = await generate_suggestions()
        return result
    except Exception as exc:
        logger.exception("Failed to refresh AI suggestions")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
