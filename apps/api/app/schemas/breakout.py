from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActiveBreakoutOut(BaseModel):
    symbol: str
    trigger_type: str
    direction: str
    status: str
    reference_level: float
    last_price: float | None = None
    triggered_at: datetime | None = None
    bars_confirmed: int = 0
    score: float | None = None


class BreakoutEventOut(BaseModel):
    id: UUID
    symbol: str
    trigger_type: str
    direction: str
    reference_level: float
    trigger_price: float
    confirmation_price: float | None
    score: float | None
    triggered_at: datetime
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}


class SymbolBreakoutsOut(BaseModel):
    symbol: str
    active: list[ActiveBreakoutOut]
    recent_events: list[BreakoutEventOut]
