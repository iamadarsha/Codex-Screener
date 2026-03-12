from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.market import IndexData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["indices"])


@router.get("/api/indices", response_model=list[IndexData])
async def get_indices():
    """Get NSE indices data using the NSE fallback service."""
    try:
        from app.services.nse_fallback import NSEClient

        client = NSEClient()
        indices = await client.get_indices()
        return [IndexData(**idx) for idx in indices]
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
