from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.ohlcv import Ohlcv1Min, OhlcvDaily
from app.schemas.market import LivePrice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/live/{symbol}", response_model=LivePrice)
async def get_live_price(symbol: str):
    """Get current LTP for a symbol from Redis."""
    try:
        from app.services.redis_cache import get_json

        data = await get_json(f"price:{symbol.upper()}")
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No live price for {symbol}",
            )
        return LivePrice(symbol=symbol.upper(), **data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch live price")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/live", response_model=list[LivePrice])
async def get_batch_prices(
    symbols: str = Query(
        ..., description="Comma-separated list of symbols"
    ),
):
    """Get live prices for multiple symbols."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        return []
    if len(symbol_list) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 symbols per request")

    results: list[LivePrice] = []
    try:
        from app.services.redis_cache import get_json

        for sym in symbol_list:
            data = await get_json(f"price:{sym}")
            if data:
                results.append(LivePrice(symbol=sym, **data))
            else:
                results.append(LivePrice(symbol=sym, ltp=0))
    except Exception as exc:
        logger.exception("Failed to fetch batch prices")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return results


@router.get("/history/{symbol}")
async def get_price_history(
    symbol: str,
    timeframe: str = Query("1d", description="1m or 1d"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Get OHLCV history from DB."""
    symbol = symbol.upper()

    if timeframe == "1m":
        query = (
            select(Ohlcv1Min)
            .where(Ohlcv1Min.symbol == symbol)
            .order_by(Ohlcv1Min.ts.desc())
            .limit(limit)
        )
        if from_date:
            query = query.where(Ohlcv1Min.ts >= from_date)
        if to_date:
            query = query.where(Ohlcv1Min.ts <= to_date)
    else:
        query = (
            select(OhlcvDaily)
            .where(OhlcvDaily.symbol == symbol)
            .order_by(OhlcvDaily.date.desc())
            .limit(limit)
        )
        if from_date:
            query = query.where(OhlcvDaily.date >= from_date)
        if to_date:
            query = query.where(OhlcvDaily.date <= to_date)

    rows = (await db.execute(query)).scalars().all()

    items = []
    for r in rows:
        if timeframe == "1m":
            items.append(
                {
                    "symbol": r.symbol,
                    "ts": r.ts.isoformat(),
                    "open": float(r.open),
                    "high": float(r.high),
                    "low": float(r.low),
                    "close": float(r.close),
                    "volume": r.volume,
                }
            )
        else:
            items.append(
                {
                    "symbol": r.symbol,
                    "date": r.date.isoformat(),
                    "open": float(r.open),
                    "high": float(r.high),
                    "low": float(r.low),
                    "close": float(r.close),
                    "volume": r.volume,
                    "week_high_52": float(r.week_high_52) if r.week_high_52 else None,
                    "week_low_52": float(r.week_low_52) if r.week_low_52 else None,
                }
            )

    return {"symbol": symbol, "timeframe": timeframe, "count": len(items), "data": items}


@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    """Get current technical indicators for a symbol from Redis."""
    try:
        from app.services.redis_cache import get_json

        data = await get_json(f"indicators:{symbol.upper()}")
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No indicators for {symbol}",
            )
        return {"symbol": symbol.upper(), "indicators": data}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch indicators")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
