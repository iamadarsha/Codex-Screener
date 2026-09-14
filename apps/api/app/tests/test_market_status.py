"""`GET /api/market/status` — holiday-aware market status. Before this, the
check only looked at the 09:15-15:30 IST clock window + weekday, so it
reported "open" on trading holidays (caught live on Ganesh Chaturthi,
2026-09-14, where NSE's own market_status() disagreed with our check)."""

from __future__ import annotations

import json
from datetime import datetime as real_datetime
from datetime import timedelta, timezone
from unittest.mock import patch

from app.api.routes.market import _next_open_skipping_weekends_and_holidays
from app.utils.redis_keys import market_holidays_key

IST = timezone(timedelta(hours=5, minutes=30))


class _FixedDatetime(real_datetime):
    """Subclass so `.replace()`/`.weekday()`/`.date()` etc. still behave like
    a real datetime — only `.now()` is pinned."""

    _fixed: real_datetime

    @classmethod
    def now(cls, tz=None):
        return cls._fixed if tz is None else cls._fixed.astimezone(tz)


def _fixed_at(iso: str) -> type[_FixedDatetime]:
    fixed = real_datetime.fromisoformat(iso)
    return type("_Fixed", (_FixedDatetime,), {"_fixed": fixed})


def test_next_open_skips_weekend():
    # Friday 16:00 IST -> next open should be Monday 09:15, not Saturday
    friday = real_datetime(2026, 9, 11, 16, 0, tzinfo=IST)
    result = _next_open_skipping_weekends_and_holidays(friday + timedelta(days=1), holidays=set())

    assert result.weekday() == 0  # Monday
    assert result.time().isoformat() == "09:15:00"


def test_next_open_skips_a_known_holiday():
    # Sunday -> Monday is a known holiday -> should roll to Tuesday
    sunday = real_datetime(2026, 9, 13, 12, 0, tzinfo=IST)
    monday_iso = "2026-09-14"
    result = _next_open_skipping_weekends_and_holidays(
        sunday + timedelta(days=1), holidays={monday_iso}
    )

    assert result.date().isoformat() == "2026-09-15"


async def test_market_status_reports_closed_on_a_known_holiday(fake_redis, api_client):
    # Ganesh Chaturthi, 2026-09-14 — a Monday, within normal trading hours,
    # but a confirmed NSE equity-segment holiday.
    await fake_redis.set(market_holidays_key(), json.dumps(["2026-09-14"]))
    fixed = _fixed_at("2026-09-14T12:00:00+05:30")

    with patch("app.api.routes.market.datetime", fixed):
        resp = await api_client.get("/api/market/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_open"] is False
    assert body["status"] == "closed"
    assert "holiday" in body["message"].lower()


async def test_market_status_reports_open_during_trading_hours_on_a_non_holiday(fake_redis, api_client):
    await fake_redis.set(market_holidays_key(), json.dumps(["2026-09-14"]))
    # A Tuesday, not in the holiday set, within trading hours.
    fixed = _fixed_at("2026-09-15T12:00:00+05:30")

    with patch("app.api.routes.market.datetime", fixed):
        resp = await api_client.get("/api/market/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_open"] is True
    assert body["status"] == "open"


async def test_market_status_fails_open_when_holiday_cache_is_empty(api_client):
    # No holiday cache populated at all (e.g. nse_poller hasn't refreshed it
    # yet) — must not crash, must fall back to the clock-only behavior.
    fixed = _fixed_at("2026-09-15T12:00:00+05:30")

    with patch("app.api.routes.market.datetime", fixed):
        resp = await api_client.get("/api/market/status")

    assert resp.status_code == 200
    assert resp.json()["is_open"] is True
