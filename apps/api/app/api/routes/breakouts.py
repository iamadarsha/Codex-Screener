from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.breakouts.engine import get_breakout_state_store
from app.breakouts.state_machine import BreakoutTracker
from app.breakouts.types import BreakoutStatus
from app.db.models.breakout_event import BreakoutEvent
from app.schemas.breakout import ActiveBreakoutOut, BreakoutEventOut, SymbolBreakoutsOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/breakouts", tags=["breakouts"])


def _to_active_out(tracker: BreakoutTracker) -> ActiveBreakoutOut:
    return ActiveBreakoutOut(
        symbol=tracker.symbol,
        trigger_type=tracker.trigger_type.value,
        direction=tracker.direction.value,
        status=tracker.status.value,
        reference_level=float(tracker.level) if tracker.level is not None else 0.0,
        last_price=float(tracker.last_price) if tracker.last_price is not None else None,
        triggered_at=tracker.triggered_at,
        bars_confirmed=tracker.bars_confirmed,
        score=None,
    )


@router.get("/active", response_model=list[ActiveBreakoutOut])
async def list_active_breakouts(
    trigger_type: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    """Currently TRIGGERED or CONFIRMED breakouts, in-memory (see
    `BreakoutStateStore` — restart resets ARMED/TRIGGERED progress, but
    every actual CONFIRMED event is separately durable via `/api/breakouts/{symbol}`).
    """
    store = get_breakout_state_store()
    trackers = store.all_active()
    if trigger_type:
        trackers = [t for t in trackers if t.trigger_type.value == trigger_type]
    trackers = trackers[:limit]
    return [_to_active_out(t) for t in trackers]


@router.get("/{symbol}", response_model=SymbolBreakoutsOut)
async def get_symbol_breakouts(symbol: str, db: AsyncSession = Depends(get_db)):
    sym = symbol.upper()
    store = get_breakout_state_store()
    active = [
        t for t in store.for_symbol(sym)
        if t.status in (BreakoutStatus.TRIGGERED, BreakoutStatus.CONFIRMED)
    ]

    rows = (
        await db.execute(
            select(BreakoutEvent)
            .where(BreakoutEvent.symbol == sym)
            .order_by(BreakoutEvent.confirmed_at.desc())
            .limit(20)
        )
    ).scalars().all()

    return SymbolBreakoutsOut(
        symbol=sym,
        active=[_to_active_out(t) for t in active],
        recent_events=[BreakoutEventOut.model_validate(r) for r in rows],
    )
