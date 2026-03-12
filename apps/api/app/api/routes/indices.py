from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.market import IndexData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["indices"])


MAJOR_INDICES = {
    "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
    "NIFTY AUTO", "NIFTY FMCG", "INDIA VIX", "NIFTY MIDCAP 50",
}


@router.get("/api/indices", response_model=list[IndexData])
async def get_indices():
    """Get NSE indices data using the NSE fallback service."""
    # Try Redis cache first (populated by NSE poller)
    try:
        from app.services.redis_cache import get_json

        cached = await get_json("market:indices")
        if cached:
            return [IndexData(**idx) for idx in cached]
    except Exception:
        pass

    # Fallback: fetch directly from NSE
    try:
        from app.services.nse_fallback import NSEClient

        client = NSEClient()
        raw = await client.get_indices()
        data = raw.get("data", []) if isinstance(raw, dict) else []
        results = []
        for idx in data:
            name = idx.get("index", "")
            if name in MAJOR_INDICES:
                results.append(
                    IndexData(
                        name=idx["index"],
                        last=idx["last"],
                        change=idx["change"],
                        change_pct=idx["percentChange"],
                        open=idx.get("open"),
                        high=idx.get("high"),
                        low=idx.get("low"),
                        prev_close=idx.get("previousClose"),
                    )
                )
        return results
    except Exception as exc:
        logger.exception("Failed to fetch NSE indices")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/data/nse/quote/{symbol}")
async def get_nse_quote(symbol: str):
    """Get NSE quote as fallback data source."""
    try:
        from app.services.nse_fallback import NSEClient

        client = NSEClient()
        quote = await client.get_quote(symbol.upper())
        if not quote:
            raise HTTPException(
                status_code=404, detail=f"No NSE quote for {symbol}"
            )
        return quote
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch NSE quote")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
