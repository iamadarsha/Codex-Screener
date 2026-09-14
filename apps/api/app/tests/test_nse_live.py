"""`app.services.nse_live` — the free, first-party NSE data wrapper around
jugaad-data's NSELive, which replaced the old blocked equity-stockIndices
scrape. Mocks `_nse_live_client()` so no real network call is made."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from app.services.nse_live import (
    fetch_bulk_quotes,
    fetch_holiday_dates,
    fetch_market_status,
)


class _FakeNSELive:
    def __init__(self, live_index_result=None, holiday_result=None, market_status_result=None, raise_on=None):
        self._live_index_result = live_index_result
        self._holiday_result = holiday_result
        self._market_status_result = market_status_result
        self._raise_on = raise_on or set()

    def live_index(self, index):
        if "live_index" in self._raise_on:
            raise RuntimeError("boom")
        return self._live_index_result

    def holiday_list(self):
        if "holiday_list" in self._raise_on:
            raise RuntimeError("boom")
        return self._holiday_result

    def market_status(self):
        if "market_status" in self._raise_on:
            raise RuntimeError("boom")
        return self._market_status_result


async def test_fetch_bulk_quotes_returns_data_list():
    fake = _FakeNSELive(live_index_result={"data": [{"symbol": "RELIANCE", "lastPrice": 1257.5}], "marketStatus": {}})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_bulk_quotes("NIFTY 500")

    assert result == [{"symbol": "RELIANCE", "lastPrice": 1257.5}]


async def test_fetch_bulk_quotes_handles_missing_data_key():
    fake = _FakeNSELive(live_index_result={"marketStatus": {}})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_bulk_quotes("NIFTY 500")

    assert result == []


async def test_fetch_bulk_quotes_propagates_exceptions():
    fake = _FakeNSELive(raise_on={"live_index"})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        with pytest.raises(RuntimeError):
            await fetch_bulk_quotes("NIFTY 500")


async def test_fetch_holiday_dates_parses_cbm_segment():
    fake = _FakeNSELive(
        holiday_result={
            "CBM": [
                {"tradingDate": "14-Sep-2026", "description": "Ganesh Chaturthi"},
                {"tradingDate": "26-Jan-2026", "description": "Republic Day"},
            ],
            "FO": [{"tradingDate": "01-Jan-2026", "description": "irrelevant segment"}],
        }
    )
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_holiday_dates()

    assert result == {date(2026, 9, 14), date(2026, 1, 26)}


async def test_fetch_holiday_dates_skips_malformed_entries():
    fake = _FakeNSELive(
        holiday_result={
            "CBM": [
                {"tradingDate": "not-a-date"},
                {"description": "missing tradingDate entirely"},
                {"tradingDate": "14-Sep-2026"},
            ]
        }
    )
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_holiday_dates()

    assert result == {date(2026, 9, 14)}


async def test_fetch_holiday_dates_fails_open_on_exception():
    fake = _FakeNSELive(raise_on={"holiday_list"})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_holiday_dates()

    assert result == set()


async def test_fetch_market_status_returns_none_on_exception():
    fake = _FakeNSELive(raise_on={"market_status"})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_market_status()

    assert result is None


async def test_fetch_market_status_returns_payload():
    fake = _FakeNSELive(market_status_result={"marketState": [{"market": "Capital Market", "marketStatus": "Close"}]})
    with patch("app.services.nse_live._nse_live_client", return_value=fake):
        result = await fetch_market_status()

    assert result["marketState"][0]["marketStatus"] == "Close"
