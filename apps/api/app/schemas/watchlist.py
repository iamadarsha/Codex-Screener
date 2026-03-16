from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WatchlistItemOut(BaseModel):
    symbol: str
    company_name: str | None = None
    position: int
    added_at: datetime
    ltp: float | None = None
    change: float | None = None
    change_pct: float | None = None

    model_config = {"from_attributes": True}


class WatchlistAddRequest(BaseModel):
    symbol: str


class WatchlistReorderRequest(BaseModel):
    symbols: list[str]  # ordered list of symbols
