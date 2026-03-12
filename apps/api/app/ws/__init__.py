"""WebSocket transport package."""

from __future__ import annotations

from fastapi import APIRouter

from app.ws import alerts as ws_alerts
from app.ws import prices as ws_prices
from app.ws import scans as ws_scans

ws_router = APIRouter()
ws_router.include_router(ws_prices.router)
ws_router.include_router(ws_scans.router)
ws_router.include_router(ws_alerts.router)
