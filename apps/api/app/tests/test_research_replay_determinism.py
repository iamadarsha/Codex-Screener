"""Running the same `replay_scan` call twice against the same fixture must
produce identical results — scan_hash, signals, and evidence status."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.research.replay import build_scan_hash, replay_scan
from app.utils.time import IST
import datetime as _dt

AS_OF = _dt.datetime(2026, 2, 10, tzinfo=IST)


def _daily_candles(start_close: float, step: float, count: int) -> list[dict]:
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
    histories = {
        "RELIANCE": _daily_candles(start_close=300.0, step=-5.0, count=25),
        "TCS": _daily_candles(start_close=100.0, step=5.0, count=25),
    }

    async def _fake_fetch(symbol: str, timeframe: str, as_of):
        return histories[symbol]

    monkeypatch.setattr("app.research.replay.fetch_candle_history_as_of", _fake_fetch)
    return histories


async def test_replay_scan_is_deterministic_across_repeated_runs(patched_history):
    scan_definition = {
        "conditions": [{"indicator": "rsi_14", "operator": "lt", "value": 30}],
        "timeframe": "1d",
    }

    result_1 = await replay_scan(
        run_id="det_run_1",
        scan_definition=scan_definition,
        universe_symbols=["RELIANCE", "TCS"],
        as_of=AS_OF,
        timeframe="1d",
    )
    result_2 = await replay_scan(
        run_id="det_run_2",
        scan_definition=scan_definition,
        universe_symbols=["RELIANCE", "TCS"],
        as_of=AS_OF,
        timeframe="1d",
    )

    assert result_1["status"] == result_2["status"] == "SUCCEEDED"
    assert result_1["signals"] == result_2["signals"]
    assert result_1["evidence"]["status"] == result_2["evidence"]["status"]
    assert result_1["summary"] == result_2["summary"]

    hash_1 = build_scan_hash(scan_definition)
    hash_2 = build_scan_hash(scan_definition)
    assert hash_1 == hash_2
    assert result_1["evidence"]["sources"] == result_2["evidence"]["sources"]
