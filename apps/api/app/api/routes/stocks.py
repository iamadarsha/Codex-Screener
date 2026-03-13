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

FALLBACK_STOCKS = [
    {"symbol": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Energy", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TCS", "company_name": "Tata Consultancy Services Ltd", "sector": "IT", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "INFY", "company_name": "Infosys Ltd", "sector": "IT", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BHARTIARTL", "company_name": "Bharti Airtel Ltd", "sector": "Telecom", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "SBIN", "company_name": "State Bank of India", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "LT", "company_name": "Larsen & Toubro Ltd", "sector": "Infrastructure", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ITC", "company_name": "ITC Ltd", "sector": "FMCG", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "KOTAKBANK", "company_name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd", "sector": "FMCG", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BAJFINANCE", "company_name": "Bajaj Finance Ltd", "sector": "NBFC", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "AXISBANK", "company_name": "Axis Bank Ltd", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "MARUTI", "company_name": "Maruti Suzuki India Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "SUNPHARMA", "company_name": "Sun Pharmaceutical Industries", "sector": "Pharma", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TATASTEEL", "company_name": "Tata Steel Ltd", "sector": "Metals", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "WIPRO", "company_name": "Wipro Ltd", "sector": "IT", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "NTPC", "company_name": "NTPC Ltd", "sector": "Power", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "POWERGRID", "company_name": "Power Grid Corporation", "sector": "Power", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "M&M", "company_name": "Mahindra & Mahindra Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ASIANPAINT", "company_name": "Asian Paints Ltd", "sector": "Consumer", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ONGC", "company_name": "Oil & Natural Gas Corp", "sector": "Energy", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TITAN", "company_name": "Titan Company Ltd", "sector": "Consumer", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ADANIENT", "company_name": "Adani Enterprises Ltd", "sector": "Conglomerate", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ULTRACEMCO", "company_name": "UltraTech Cement Ltd", "sector": "Cement", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BAJAJFINSV", "company_name": "Bajaj Finserv Ltd", "sector": "NBFC", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "JSWSTEEL", "company_name": "JSW Steel Ltd", "sector": "Metals", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TECHM", "company_name": "Tech Mahindra Ltd", "sector": "IT", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HCLTECH", "company_name": "HCL Technologies Ltd", "sector": "IT", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "COALINDIA", "company_name": "Coal India Ltd", "sector": "Mining", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "DRREDDY", "company_name": "Dr Reddy's Laboratories", "sector": "Pharma", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "INDUSINDBK", "company_name": "IndusInd Bank Ltd", "sector": "Banking", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "NESTLEIND", "company_name": "Nestle India Ltd", "sector": "FMCG", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "CIPLA", "company_name": "Cipla Ltd", "sector": "Pharma", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "GRASIM", "company_name": "Grasim Industries Ltd", "sector": "Cement", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "APOLLOHOSP", "company_name": "Apollo Hospitals Enterprise", "sector": "Healthcare", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HEROMOTOCO", "company_name": "Hero MotoCorp Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "EICHERMOT", "company_name": "Eicher Motors Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "DIVISLAB", "company_name": "Divi's Laboratories Ltd", "sector": "Pharma", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BPCL", "company_name": "Bharat Petroleum Corp", "sector": "Energy", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TATACONSUM", "company_name": "Tata Consumer Products", "sector": "FMCG", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "SBILIFE", "company_name": "SBI Life Insurance", "sector": "Insurance", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BRITANNIA", "company_name": "Britannia Industries Ltd", "sector": "FMCG", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HDFCLIFE", "company_name": "HDFC Life Insurance", "sector": "Insurance", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "ADANIPORTS", "company_name": "Adani Ports & SEZ Ltd", "sector": "Infrastructure", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "HINDALCO", "company_name": "Hindalco Industries Ltd", "sector": "Metals", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "BAJAJ-AUTO", "company_name": "Bajaj Auto Ltd", "sector": "Automobile", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "SHRIRAMFIN", "company_name": "Shriram Finance Ltd", "sector": "NBFC", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
    {"symbol": "TRENT", "company_name": "Trent Ltd", "sector": "Retail", "is_nifty50": True, "is_nifty500": True, "is_fno": True},
]


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

    # If DB is empty, use fallback data
    if total == 0:
        fallback = FALLBACK_STOCKS
        if search:
            pattern = search.lower()
            fallback = [s for s in fallback if pattern in s["symbol"].lower() or pattern in s["company_name"].lower()]
        fb_total = len(fallback)
        offset = (page - 1) * page_size
        fb_page = fallback[offset:offset + page_size]
        total_pages = max(1, (fb_total + page_size - 1) // page_size)
        return StockList(
            items=[StockOut(**s) for s in fb_page],
            total=fb_total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

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

    if not rows:
        # Fallback to hardcoded data if DB is empty
        q_lower = q.lower()
        matches = [
            StockSearch(**s)
            for s in FALLBACK_STOCKS
            if q_lower in s["symbol"].lower() or q_lower in s["company_name"].lower()
        ][:limit]
        return matches

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
        # Try fallback data
        fb = next((s for s in FALLBACK_STOCKS if s["symbol"] == symbol.upper()), None)
        if fb:
            return StockOut(**fb)
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
