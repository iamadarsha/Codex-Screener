from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LivePrice(BaseModel):
    symbol: str
    ltp: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    change: float | None = None
    change_pct: float | None = None
    timestamp: datetime | None = None


class IndexData(BaseModel):
    name: str
    symbol: str | None = None
    last: float
    change: float
    change_pct: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    prev_close: float | None = None
    timestamp: datetime | None = None


class MarketStatus(BaseModel):
    is_open: bool
    status: str  # "open", "closed", "pre_open", "post_close"
    next_open: datetime | None = None
    next_close: datetime | None = None
    message: str | None = None


class MarketBreadth(BaseModel):
    advances: int
    declines: int
    unchanged: int
    total: int
    advance_decline_ratio: float | None = None


class SectorPerformance(BaseModel):
    sector: str
    change_pct: float
    advances: int
    declines: int
    top_gainer: str | None = None
    top_loser: str | None = None
