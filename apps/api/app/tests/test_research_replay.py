"""End-to-end `replay_scan` test against a synthetic candle fixture.

`fetch_candle_history_as_of` itself is monkeypatched here (returning fixed,
pre-built candle histories per symbol) so this test focuses purely on
`replay_scan`'s orchestration — indicator replay, evidence gating,
condition evaluation, signal assembly. The as-of SQL-filtering behavior of
the real `fetch_candle_history_as_of` is proven separately and rigorously
in `test_research_replay_future_leakage.py`.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.research.replay import replay_scan
from app.utils.time import IST
import datetime as _dt

AS_OF = _dt.datetime(2026, 2, 10, tzinfo=IST)


def _daily_candles(start_close: float, step: float, count: int) -> list[dict]:
    """A monotonic daily candle series — strictly decreasing (step<0) drives
    RSI toward 0, strictly increasing (step>0) drives RSI toward 100."""
    start = date(2026, 1, 1)
    candles = []
    close = start_close
    for i in range(count):
        d = start + timedelta(days=i)
        candles.append(
            {
                "ts": d.isoformat(),
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 10_000,
            }
        )
        close += step
    return candles


@pytest.fixture
def patched_history(monkeypatch):
    """Fixed per-symbol candle histories: RELIANCE trends sharply down
    (RSI should plunge below 30), TCS trends sharply up (RSI should stay
    high, well above 30)."""
    histories = {
        "RELIANCE": _daily_candles(start_close=300.0, step=-5.0, count=25),
        "TCS": _daily_candles(start_close=100.0, step=5.0, count=25),
    }

    async def _fake_fetch(symbol: str, timeframe: str, as_of):
        return histories[symbol]

    monkeypatch.setattr("app.research.replay.fetch_candle_history_as_of", _fake_fetch)
    return histories


async def test_replay_scan_reaches_succeeded_with_expected_signal(patched_history):
    scan_definition = {
        "conditions": [{"indicator": "rsi_14", "operator": "lt", "value": 30}],
        "timeframe": "1d",
    }

    result = await replay_scan(
        run_id="test_run_1",
        scan_definition=scan_definition,
        universe_symbols=["RELIANCE", "TCS"],
        as_of=AS_OF,
        timeframe="1d",
    )

    assert result["status"] == "SUCCEEDED"
    assert result["evidence"]["status"] == "valid"

    matched_symbols = {s["symbol"] for s in result["signals"]}
    assert matched_symbols == {"RELIANCE"}
    assert "TCS" not in matched_symbols

    reliance_signal = next(s for s in result["signals"] if s["symbol"] == "RELIANCE")
    assert reliance_signal["indicator_snapshot"]["rsi_14"] < 30
    assert result["summary"]["symbols_checked"] == 2
    assert result["summary"]["signals"] == 1


async def test_replay_scan_with_pattern_filter_only(patched_history):
    scan_definition = {"pattern": "nonexistent_pattern_name", "timeframe": "1d"}

    result = await replay_scan(
        run_id="test_run_2",
        scan_definition=scan_definition,
        universe_symbols=["RELIANCE"],
        as_of=AS_OF,
        timeframe="1d",
    )

    assert result["status"] == "SUCCEEDED"
    assert result["signals"] == []  # pattern never matches -> no signals, but still SUCCEEDED


async def test_replay_scan_with_no_filter_returns_no_signals(patched_history):
    scan_definition = {"timeframe": "1d"}

    result = await replay_scan(
        run_id="test_run_3",
        scan_definition=scan_definition,
        universe_symbols=["RELIANCE", "TCS"],
        as_of=AS_OF,
        timeframe="1d",
    )

    assert result["status"] == "SUCCEEDED"
    assert result["signals"] == []
