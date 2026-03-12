from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.stock import Stock
from app.schemas.stock import StockList, StockOut, StockSearch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=StockList)
async def list_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, description="Search symbol or company name"),
    nifty50: bool | None = Query(None),
    nifty500: bool | None = Query(None),
    fno: bool | None = Query(None),
    sector: str | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List stocks with pagination, search, and filters."""
    query = select(Stock)
    count_query = select(func.count()).select_from(Stock)

    if active_only:
        query = query.where(Stock.is_active.is_(True))
        count_query = count_query.where(Stock.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        search_filter = or_(
            Stock.symbol.ilike(pattern),
            Stock.company_name.ilike(pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if nifty50 is not None:
        query = query.where(Stock.is_nifty50 == nifty50)
        count_query = count_query.where(Stock.is_nifty50 == nifty50)
    if nifty500 is not None:
        query = query.where(Stock.is_nifty500 == nifty500)
        count_query = count_query.where(Stock.is_nifty500 == nifty500)
    if fno is not None:
        query = query.where(Stock.is_fno == fno)
        count_query = count_query.where(Stock.is_fno == fno)
    if sector:
        query = query.where(Stock.sector == sector)
        count_query = count_query.where(Stock.sector == sector)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            query.order_by(Stock.symbol).offset(offset).limit(page_size)
        )
    ).scalars().all()

    items = []
    for row in rows:
        item = StockOut.model_validate(row)
        # Try to enrich with live price from Redis
        try:
            from app.services.redis_cache import get_json

            price_data = await get_json(f"price:{row.symbol}")
            if price_data:
                item.ltp = price_data.get("ltp")
                item.change = price_data.get("change")
                item.change_pct = price_data.get("change_pct")
        except Exception:
            pass
        items.append(item)

    total_pages = max(1, (total + page_size - 1) // page_size)
    return StockList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/search", response_model=list[StockSearch])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search stocks by symbol or company name."""
    pattern = f"%{q}%"
    query = (
        select(Stock)
        .where(
            Stock.is_active.is_(True),
            or_(
                Stock.symbol.ilike(pattern),
                Stock.company_name.ilike(pattern),
            ),
        )
        .order_by(Stock.symbol)
        .limit(limit)
    )
    rows = (await db.execute(query)).scalars().all()
    return [StockSearch.model_validate(r) for r in rows]


@router.get("/{symbol}", response_model=StockOut)
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get stock detail with current price from Redis."""
    row = (
        await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    item = StockOut.model_validate(row)
    try:
        from app.services.redis_cache import get_json

        price_data = await get_json(f"price:{row.symbol}")
        if price_data:
            item.ltp = price_data.get("ltp")
            item.change = price_data.get("change")
            item.change_pct = price_data.get("change_pct")
    except Exception:
        pass
    return item
