from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.stock import Stock
from app.schemas.fundamentals import FundamentalFilters, FundamentalResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fundamentals", tags=["fundamentals"])


@router.get("", response_model=dict)
async def filter_fundamentals(
    pe_min: float | None = Query(None),
    pe_max: float | None = Query(None),
    pb_min: float | None = Query(None),
    pb_max: float | None = Query(None),
    roe_min: float | None = Query(None),
    roe_max: float | None = Query(None),
    market_cap_min: float | None = Query(None),
    market_cap_max: float | None = Query(None),
    debt_equity_max: float | None = Query(None),
    div_yield_min: float | None = Query(None),
    sector: str | None = Query(None),
    universe: str = Query("nifty500"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Filter stocks by fundamental criteria."""
    query = select(Stock).where(Stock.is_active.is_(True))
    count_query = select(func.count()).select_from(Stock).where(Stock.is_active.is_(True))

    # Universe filter
    if universe == "nifty50":
        query = query.where(Stock.is_nifty50.is_(True))
        count_query = count_query.where(Stock.is_nifty50.is_(True))
    elif universe == "nifty500":
        query = query.where(Stock.is_nifty500.is_(True))
        count_query = count_query.where(Stock.is_nifty500.is_(True))
    elif universe == "fno":
        query = query.where(Stock.is_fno.is_(True))
        count_query = count_query.where(Stock.is_fno.is_(True))

    # Fundamental filters
    if pe_min is not None:
        query = query.where(Stock.pe >= pe_min)
        count_query = count_query.where(Stock.pe >= pe_min)
    if pe_max is not None:
        query = query.where(Stock.pe <= pe_max)
        count_query = count_query.where(Stock.pe <= pe_max)
    if pb_min is not None:
        query = query.where(Stock.pb >= pb_min)
        count_query = count_query.where(Stock.pb >= pb_min)
    if pb_max is not None:
        query = query.where(Stock.pb <= pb_max)
        count_query = count_query.where(Stock.pb <= pb_max)
    if roe_min is not None:
        query = query.where(Stock.roe >= roe_min)
        count_query = count_query.where(Stock.roe >= roe_min)
    if roe_max is not None:
        query = query.where(Stock.roe <= roe_max)
        count_query = count_query.where(Stock.roe <= roe_max)
    if market_cap_min is not None:
        query = query.where(Stock.market_cap >= market_cap_min)
        count_query = count_query.where(Stock.market_cap >= market_cap_min)
    if market_cap_max is not None:
        query = query.where(Stock.market_cap <= market_cap_max)
        count_query = count_query.where(Stock.market_cap <= market_cap_max)
    if debt_equity_max is not None:
        query = query.where(Stock.debt_equity <= debt_equity_max)
        count_query = count_query.where(Stock.debt_equity <= debt_equity_max)
    if div_yield_min is not None:
        query = query.where(Stock.div_yield >= div_yield_min)
        count_query = count_query.where(Stock.div_yield >= div_yield_min)
    if sector:
        query = query.where(Stock.sector == sector)
        count_query = count_query.where(Stock.sector == sector)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            query.order_by(Stock.market_cap.desc().nullslast())
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()

    items = []
    for row in rows:
        item = FundamentalResult.model_validate(row)
        try:
            from app.services.redis_cache import get_json

            price_data = await get_json(f"price:{row.symbol}")
            if price_data:
                item.ltp = price_data.get("ltp")
                item.change_pct = price_data.get("change_pct")
        except Exception:
            pass
        items.append(item)

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{symbol}", response_model=FundamentalResult)
async def get_stock_fundamentals(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed fundamentals for a single stock."""
    row = (
        await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    item = FundamentalResult.model_validate(row)
    try:
        from app.services.redis_cache import get_json

        price_data = await get_json(f"price:{row.symbol}")
        if price_data:
            item.ltp = price_data.get("ltp")
            item.change_pct = price_data.get("change_pct")
    except Exception:
        pass
    return item
