from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.stock import Stock
from app.db.models.watchlist import WatchlistItem
from app.schemas.common import SuccessResponse
from app.schemas.watchlist import (
    WatchlistAddRequest,
    WatchlistItemOut,
    WatchlistReorderRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemOut])
async def get_watchlist(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's watchlist items with live prices."""
    uid = uuid.UUID(user_id)
    query = (
        select(WatchlistItem, Stock.company_name)
        .join(Stock, WatchlistItem.symbol == Stock.symbol)
        .where(WatchlistItem.user_id == uid)
        .order_by(WatchlistItem.position)
    )
    rows = (await db.execute(query)).all()

    items: list[WatchlistItemOut] = []
    for wl_item, company_name in rows:
        out = WatchlistItemOut(
            symbol=wl_item.symbol,
            company_name=company_name,
            position=wl_item.position,
            added_at=wl_item.added_at,
        )
        try:
            from app.services.redis_cache import get_json

            price_data = await get_json(f"price:{wl_item.symbol}")
            if price_data:
                out.ltp = price_data.get("ltp")
                out.change = price_data.get("change")
                out.change_pct = price_data.get("change_pct")
        except Exception:
            pass
        items.append(out)
    return items


@router.post("", response_model=WatchlistItemOut, status_code=201)
async def add_to_watchlist(
    req: WatchlistAddRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a symbol to the user's watchlist."""
    uid = uuid.UUID(user_id)
    symbol = req.symbol.upper()

    stock = (
        await db.execute(select(Stock).where(Stock.symbol == symbol))
    ).scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    existing = (
        await db.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == uid,
                WatchlistItem.symbol == symbol,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} already in watchlist")

    max_pos = (
        await db.execute(
            select(func.max(WatchlistItem.position)).where(
                WatchlistItem.user_id == uid
            )
        )
    ).scalar_one()
    next_pos = (max_pos or 0) + 1

    item = WatchlistItem(user_id=uid, symbol=symbol, position=next_pos)
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return WatchlistItemOut(
        symbol=item.symbol,
        company_name=stock.company_name,
        position=item.position,
        added_at=item.added_at,
    )


@router.delete("/{symbol}", response_model=SuccessResponse)
async def remove_from_watchlist(
    symbol: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a symbol from the user's watchlist."""
    uid = uuid.UUID(user_id)
    result = await db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.user_id == uid,
            WatchlistItem.symbol == symbol.upper(),
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")
    await db.commit()
    return SuccessResponse(message=f"{symbol} removed from watchlist")


@router.put("/reorder", response_model=SuccessResponse)
async def reorder_watchlist(
    req: WatchlistReorderRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder watchlist items."""
    uid = uuid.UUID(user_id)
    for idx, symbol in enumerate(req.symbols):
        await db.execute(
            update(WatchlistItem)
            .where(
                WatchlistItem.user_id == uid,
                WatchlistItem.symbol == symbol.upper(),
            )
            .values(position=idx + 1)
        )
    await db.commit()
    return SuccessResponse(message="Watchlist reordered")
