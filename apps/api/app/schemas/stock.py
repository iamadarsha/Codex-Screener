from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class StockOut(BaseModel):
    symbol: str
    isin: str | None = None
    instrument_key: str | None = None
    company_name: str
    exchange: str = "NSE"
    sector: str | None = None
    market_cap: Decimal | None = None
    pe: Decimal | None = None
    pb: Decimal | None = None
    roe: Decimal | None = None
    debt_equity: Decimal | None = None
    div_yield: Decimal | None = None
    is_nifty50: bool = False
    is_nifty500: bool = False
    is_fno: bool = False
    is_active: bool = True
    ltp: float | None = None
    change: float | None = None
    change_pct: float | None = None

    model_config = {"from_attributes": True}


class StockList(BaseModel):
    items: list[StockOut]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_pages: int


class StockSearch(BaseModel):
    symbol: str
    company_name: str
    sector: str | None = None
    is_nifty50: bool = False
    is_nifty500: bool = False

    model_config = {"from_attributes": True}
