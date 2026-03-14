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


@router.get("/debug")
async def debug_ai_suggestions():
    """Debug endpoint — shows what data is available for AI suggestion generation."""
    from app.services.redis_cache import get_redis
    from app.services.ai_suggestions import (
        _ensure_symbol_lookup, _SYMBOL_META, _SEED_PATH,
        _extract_headline_symbols, _fetch_news_headlines,
    )

    r = await get_redis()

    # Count price keys
    price_keys = []
    async for key in r.scan_iter(match="price:*", count=500):
        price_keys.append(key)

    # Count indicator keys
    ind_keys = []
    async for key in r.scan_iter(match="ind:*:1d", count=500):
        ind_keys.append(key)

    # Check seed file
    _ensure_symbol_lookup()
    seed_exists = _SEED_PATH.exists()
    seed_count = len(_SYMBOL_META)

    # Sample a price key
    sample_price = None
    if price_keys:
        raw = await r.get(price_keys[0])
        sample_price = {"key": price_keys[0], "value": raw[:200] if raw else None}

    # Check headlines
    try:
        headlines = await asyncio.wait_for(_fetch_news_headlines(), timeout=15)
    except Exception:
        headlines = []

    headline_symbols = _extract_headline_symbols(headlines) if headlines else {}

    return {
        "price_key_count": len(price_keys),
        "indicator_key_count": len(ind_keys),
        "seed_path": str(_SEED_PATH),
        "seed_exists": seed_exists,
        "seed_symbol_count": seed_count,
        "headline_count": len(headlines),
        "headline_symbol_matches": len(headline_symbols),
        "matched_symbols": list(headline_symbols.keys())[:20],
        "sample_price": sample_price,
        "sample_price_keys": price_keys[:5],
        "sample_ind_keys": ind_keys[:5],
    }
