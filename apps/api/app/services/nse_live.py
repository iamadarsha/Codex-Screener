"""Free, first-party NSE data via `jugaad-data`'s NSELive client.

Replaces the old `nse_poller.py` scrape of `/api/equity-stockIndices`,
which was confirmed (2026-09-14, live, during trading hours) to be
blocked by NSE's bot-detection — the homepage itself returned 403 and
the data endpoint returned a bot-challenge page disguised as a 404.
`NSELive`'s endpoints succeed from the same VM/IP with no blocking,
returning real structured data (verified against RELIANCE's actual
quote and the official NSE holiday calendar on the same date).

`NSELive.live_index("NIFTY 500")` returns all ~500 constituents (plus
the index's own summary row) in a single fast call (~0.2s observed) —
this is the key discovery that makes a free, complete-universe fallback
feed viable without per-symbol calls or any LLM involvement.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_HOLIDAY_SEGMENT = "CBM"  # Capital/Cash Market segment = equities


def _nse_live_client():
    from jugaad_data.nse import NSELive

    return NSELive()


async def fetch_bulk_quotes(index: str = "NIFTY 500") -> list[dict[str, Any]]:
    """Fetch every constituent's quote for *index* in one call.

    Returns the raw per-stock dict list from NSE (symbol, lastPrice,
    open, dayHigh, dayLow, previousClose, change, pChange,
    totalTradedVolume, ...). The index's own summary row (symbol equal
    to the index name) is included — callers filter it out.

    Raises on failure — callers decide fallback/retry behavior, matching
    this codebase's convention elsewhere (e.g. `yahoo_finance.py`).
    """

    def _sync_fetch() -> list[dict[str, Any]]:
        nse = _nse_live_client()
        result = nse.live_index(index)
        return result.get("data", []) if isinstance(result, dict) else []

    return await asyncio.to_thread(_sync_fetch)


async def fetch_market_status() -> dict[str, Any] | None:
    """Fetch NSE's own official market-status payload. Returns `None` on failure."""

    def _sync_fetch() -> dict[str, Any]:
        return _nse_live_client().market_status()

    try:
        return await asyncio.to_thread(_sync_fetch)
    except Exception as exc:
        log.warning("nse_market_status_fetch_failed", error=str(exc))
        return None


async def fetch_holiday_dates() -> set[date]:
    """Fetch this year's official NSE equity-segment trading holidays.

    Never raises — returns an empty set on any failure so callers fail
    open (treat as "no known holidays today") rather than block on a
    broken network call every time market status is checked.
    """

    def _sync_fetch() -> set[date]:
        raw = _nse_live_client().holiday_list()
        dates: set[date] = set()
        for entry in raw.get(_HOLIDAY_SEGMENT, []):
            trading_date = entry.get("tradingDate")
            if not trading_date:
                continue
            try:
                dates.add(datetime.strptime(trading_date, "%d-%b-%Y").date())
            except ValueError:
                continue
        return dates

    try:
        return await asyncio.to_thread(_sync_fetch)
    except Exception as exc:
        log.warning("nse_holiday_fetch_failed", error=str(exc))
        return set()
