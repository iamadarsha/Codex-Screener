"""Session VWAP reset behavior + live market_info tracking (Phase 2.1 gates)."""

from __future__ import annotations

from datetime import date

from app.market.indicators import VwapState
from app.market.session import SessionTracker


def test_vwap_accumulates_across_updates():
    vwap = VwapState()
    vwap.update(high=101, low=99, close=100, volume=1000)
    vwap.update(high=103, low=101, close=102, volume=2000)

    # Weighted toward the second (larger-volume) bar's typical price.
    assert 100.5 < vwap.value < 102.0


def test_vwap_reset_clears_accumulated_state():
    vwap = VwapState()
    vwap.update(high=200, low=190, close=195, volume=5000)
    assert vwap.value is not None

    vwap.reset()

    assert vwap.value is None
    # A fresh session's first bar should reflect only that bar, not carry
    # over any influence from the previous session's accumulated volume.
    fresh_value = vwap.update(high=101, low=99, close=100, volume=1)
    assert fresh_value == 100.0


def test_session_tracker_uses_live_market_info_when_available():
    tracker = SessionTracker()
    assert tracker.has_live_status() is False
    assert tracker.is_regular_session_live() is False

    tracker.update_from_market_info({"NSE_EQ": "NORMAL_OPEN"}, current_ts=1_700_000_000_000)

    assert tracker.has_live_status() is True
    assert tracker.is_regular_session_live("NSE_EQ") is True
    assert tracker.is_regular_session_live("NSE_FO") is False


def test_session_tracker_holiday_overrides_time_window_heuristic():
    from datetime import datetime

    from app.utils.time import IST

    a_tuesday = datetime(2026, 1, 6, 10, 0, tzinfo=IST)
    tracker = SessionTracker(holidays={date(2026, 1, 6)})

    assert tracker.is_market_open_heuristic(a_tuesday) is False
