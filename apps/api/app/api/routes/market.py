from __future__ import annotations

import logging
from datetime import datetime, time, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.stock import Stock
from app.schemas.market import (
    IndexData,
    MarketBreadth,
    MarketStatus,
    SectorPerformance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

IST = timezone(timedelta(hours=5, minutes=30))
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def _market_status_now() -> MarketStatus:
    """Determine market open/close status based on IST time."""
    now_ist = datetime.now(IST)
    current_time = now_ist.time()
    weekday = now_ist.weekday()

    # Weekend
    if weekday >= 5:
        days_until_monday = 7 - weekday
        next_open_dt = now_ist.replace(
            hour=9, minute=15, second=0, microsecond=0
        ) + timedelta(days=days_until_monday)
        return MarketStatus(
            is_open=False,
            status="closed",
            next_open=next_open_dt,
            message="Market is closed (weekend)",
        )

    if current_time < time(9, 0):
        next_open_dt = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        return MarketStatus(
            is_open=False,
            status="closed",
            next_open=next_open_dt,
            message="Market opens at 9:15 AM IST",
        )

    if time(9, 0) <= current_time < MARKET_OPEN:
        next_open_dt = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        return MarketStatus(
            is_open=False,
            status="pre_open",
            next_open=next_open_dt,
            message="Pre-open session",
        )

    if MARKET_OPEN <= current_time < MARKET_CLOSE:
        next_close_dt = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
        return MarketStatus(
            is_open=True,
            status="open",
            next_close=next_close_dt,
            message="Market is open",
        )

    # After close
    next_day = now_ist + timedelta(days=1)
    if next_day.weekday() >= 5:
        days_until_monday = 7 - next_day.weekday()
        next_day = next_day + timedelta(days=days_until_monday)
    next_open_dt = next_day.replace(hour=9, minute=15, second=0, microsecond=0)
    return MarketStatus(
        is_open=False,
        status="post_close",
        next_open=next_open_dt,
        message="Market is closed for the day",
    )


@router.get("/status", response_model=MarketStatus)
async def market_status():
    """Get current market open/closed status."""
    return _market_status_now()


@router.get("/breadth", response_model=MarketBreadth)
async def market_breadth():
    """Get advance/decline/unchanged counts from Redis."""
    try:
        from app.services.redis_cache import get_json

        data = await get_json("market:breadth")
        if data:
            return MarketBreadth(**data)
    except Exception:
        pass

    # Fallback: compute from cached prices
    advances = declines = unchanged = 0
    try:
        from app.services.redis_cache import get_redis

        redis = await get_redis()
        keys = await redis.keys("price:*")
        for key in keys:
            from app.services.redis_cache import get_json as _gj

            price_data = await _gj(key.decode() if isinstance(key, bytes) else key)
            if price_data:
                change = price_data.get("change_pct", 0) or 0
                if change > 0:
                    advances += 1
                elif change < 0:
                    declines += 1
                else:
                    unchanged += 1
    except Exception:
        pass

    total = advances + declines + unchanged
    ratio = round(advances / declines, 2) if declines > 0 else None
    return MarketBreadth(
        advances=advances,
        declines=declines,
        unchanged=unchanged,
        total=total,
        advance_decline_ratio=ratio,
    )


MAJOR_INDICES = {
    "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
    "NIFTY AUTO", "NIFTY FMCG", "INDIA VIX", "NIFTY MIDCAP 50",
}


@router.get("/indices", response_model=list[IndexData])
async def market_indices():
    """Get major NSE index values."""
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
        logger.exception("Failed to fetch indices")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sectors", response_model=list[SectorPerformance])
async def market_sectors(
    db: AsyncSession = Depends(get_db),
):
    """Get sector-wise performance summary."""
    try:
        from app.services.redis_cache import get_json

        cached = await get_json("market:sectors")
        if cached:
            return [SectorPerformance(**s) for s in cached]
    except Exception:
        pass

    # Fallback: build from DB sectors and cached prices
    query = (
        select(Stock.sector, func.count(Stock.symbol))
        .where(Stock.sector.isnot(None), Stock.is_active.is_(True))
        .group_by(Stock.sector)
        .order_by(Stock.sector)
    )
    rows = (await db.execute(query)).all()

    results: list[SectorPerformance] = []
    for sector_name, count in rows:
        if not sector_name:
            continue
        results.append(
            SectorPerformance(
                sector=sector_name,
                change_pct=0.0,
                advances=0,
                declines=0,
            )
        )
    return results
