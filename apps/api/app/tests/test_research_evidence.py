"""Truth table for `validate_evidence` — the single correctness gate a
replay run must pass before its signals can be presented as trustworthy."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.research.evidence import validate_evidence
from app.utils.time import IST

AS_OF = datetime(2026, 9, 10, 9, 17, 0, tzinfo=IST)
UNIVERSE = ["RELIANCE", "TCS"]
SCAN_HASH = "deadbeefcafef00d"


def _candle(minute_offset: int, close: float = 100.0) -> dict:
    ts = AS_OF + timedelta(minutes=minute_offset)
    return {
        "ts": ts.isoformat(),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1000,
    }


def test_all_valid_case():
    candles_by_symbol = {
        "RELIANCE": [_candle(-2), _candle(-1), _candle(0)],
        "TCS": [_candle(-2), _candle(-1), _candle(0)],
    }
    record = validate_evidence(candles_by_symbol, AS_OF, UNIVERSE, SCAN_HASH)

    assert record.status == "valid"
    assert record.future_data_detected is False
    assert all(record.checks.values())
    assert record.errors == []
    assert record.max_market_timestamp_used == AS_OF


def test_future_candle_marks_invalid_and_future_data_detected():
    candles_by_symbol = {
        "RELIANCE": [_candle(-1), _candle(0), _candle(1)],  # +1min is past as_of
    }
    record = validate_evidence(candles_by_symbol, AS_OF, ["RELIANCE"], SCAN_HASH)

    assert record.status == "invalid"
    assert record.future_data_detected is True
    assert record.checks["future_bar_check"] is False
    assert record.errors  # at least one explanatory error


def test_out_of_order_timestamps_marks_invalid():
    candles_by_symbol = {
        "RELIANCE": [_candle(-1), _candle(-2), _candle(0)],  # scrambled order
    }
    record = validate_evidence(candles_by_symbol, AS_OF, ["RELIANCE"], SCAN_HASH)

    assert record.status == "invalid"
    assert record.checks["timestamp_order_check"] is False


def test_symbol_not_in_universe_fails_universe_check():
    candles_by_symbol = {
        "RELIANCE": [_candle(0)],
        "UNKNOWNCO": [_candle(0)],
    }
    record = validate_evidence(candles_by_symbol, AS_OF, ["RELIANCE"], SCAN_HASH)

    assert record.checks["universe_check"] is False
    assert record.status == "invalid"


def test_empty_scan_hash_fails_scan_version_check():
    candles_by_symbol = {"RELIANCE": [_candle(0)]}
    record = validate_evidence(candles_by_symbol, AS_OF, ["RELIANCE"], "")

    assert record.checks["scan_version_check"] is False
    assert record.status == "invalid"


def test_empty_candle_data_for_a_symbol_is_incomplete_not_invalid():
    candles_by_symbol = {
        "RELIANCE": [_candle(-1), _candle(0)],
        "TCS": [],  # simply no data yet — not a contradiction of as_of
    }
    record = validate_evidence(candles_by_symbol, AS_OF, UNIVERSE, SCAN_HASH)

    assert record.status == "incomplete"
    assert all(record.checks.values())  # no hard violation triggered
    assert record.future_data_detected is False


def test_no_symbols_at_all_is_vacuously_valid():
    record = validate_evidence({}, AS_OF, UNIVERSE, SCAN_HASH)
    assert record.status == "valid"
    assert record.max_market_timestamp_used is None
