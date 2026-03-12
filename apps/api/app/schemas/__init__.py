"""Pydantic v2 schemas for BreakoutScan API."""

from __future__ import annotations

from app.schemas.alert import (
    AlertCreateRequest,
    AlertHistoryOut,
    AlertOut,
    AlertUpdateRequest,
)
from app.schemas.auth import AuthStatus, LoginURLResponse, TokenResponse
from app.schemas.common import ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.fundamentals import FundamentalFilters, FundamentalResult
from app.schemas.market import (
    IndexData,
    LivePrice,
    MarketBreadth,
    MarketStatus,
    SectorPerformance,
)
from app.schemas.screener import (
    CustomScanRequest,
    PrebuiltScanOut,
    ScanCondition,
    ScanRequest,
    ScanResult,
    ScanResultItem,
)
from app.schemas.stock import StockList, StockOut, StockSearch
from app.schemas.watchlist import (
    WatchlistAddRequest,
    WatchlistItemOut,
    WatchlistReorderRequest,
)

__all__ = [
    "AlertCreateRequest",
    "AlertHistoryOut",
    "AlertOut",
    "AlertUpdateRequest",
    "AuthStatus",
    "CustomScanRequest",
    "ErrorResponse",
    "FundamentalFilters",
    "FundamentalResult",
    "IndexData",
    "LivePrice",
    "LoginURLResponse",
    "MarketBreadth",
    "MarketStatus",
    "PaginatedResponse",
    "PrebuiltScanOut",
    "ScanCondition",
    "ScanRequest",
    "ScanResult",
    "ScanResultItem",
    "SectorPerformance",
    "StockList",
    "StockOut",
    "StockSearch",
    "SuccessResponse",
    "TokenResponse",
    "WatchlistAddRequest",
    "WatchlistItemOut",
    "WatchlistReorderRequest",
]
