from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ScanCondition(BaseModel):
    indicator: str  # e.g. "rsi", "sma_cross", "volume_spike"
    operator: str  # "gt", "lt", "eq", "cross_above", "cross_below"
    value: float | str | None = None
    params: dict[str, object] | None = None


class ScanRequest(BaseModel):
    scan_id: str  # prebuilt scan ID
    universe: str = "nifty500"  # "nifty50", "nifty500", "fno", "all"
    timeframe: str = "1d"


class CustomScanRequest(BaseModel):
    name: str | None = None
    conditions: list[ScanCondition] = Field(min_length=1)
    universe: str = "nifty500"
    timeframe: str = "1d"
    user_id: str | None = None


class ScanResultItem(BaseModel):
    symbol: str
    company_name: str
    ltp: float | None = None
    change_pct: float | None = None
    sector: str | None = None
    volume: float | None = None
    rsi_14: float | None = None
    ema_status: str | None = None
    signal_strength: float | None = None
    matched_conditions: list[str] | None = None
    score: float | None = None


class ScanResult(BaseModel):
    scan_id: str
    scan_name: str
    description: str | None = None
    run_at: datetime
    duration_ms: int | None = None
    total_matches: int
    items: list[ScanResultItem]


class PrebuiltScanOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str | None = None
    conditions: list[dict[str, object]] | None = None
