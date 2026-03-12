from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class FundamentalFilters(BaseModel):
    pe_min: float | None = None
    pe_max: float | None = None
    pb_min: float | None = None
    pb_max: float | None = None
    roe_min: float | None = None
    roe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    debt_equity_max: float | None = None
    div_yield_min: float | None = None
    sector: str | None = None
    universe: str = "nifty500"  # "nifty50", "nifty500", "fno", "all"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class FundamentalResult(BaseModel):
    symbol: str
    company_name: str
    sector: str | None = None
    market_cap: Decimal | None = None
    pe: Decimal | None = None
    pb: Decimal | None = None
    roe: Decimal | None = None
    debt_equity: Decimal | None = None
    div_yield: Decimal | None = None
    ltp: float | None = None
    change_pct: float | None = None

    model_config = {"from_attributes": True}
