"""`_scan_symbol()` end-to-end against `fake_redis` — reaching CONFIRMED
after the expected number of simulated scan cycles, and firing the
persistence/notification side effects on confirmation.

`now_ist` and `fetch_candle_history` are monkeypatched so the test controls
bar-boundary progression explicitly (real wall-clock time can't be relied
on to cross a 5-min boundary inside a fast unit test) and never touches a
real Postgres connection.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from app.breakouts import engine
from app.breakouts.types import BreakoutStatus, Direction, TriggerType
from app.services.redis_cache import set_json
from app.utils.redis_keys import indicator_key
from app.utils.time import IST


@dataclass
class _FakeAlert:
    id: uuid.UUID
    frequency: str = "every_time"


@pytest.fixture(autouse=True)
def _clear_engine_caches():
    engine.get_breakout_state_store.cache_clear()
    engine._indicator_states.cache_clear()  # noqa: SLF001
    engine._last_indicator_snapshot.cache_clear()  # noqa: SLF001
    engine._last_seen_candle_ts.cache_clear()  # noqa: SLF001
    engine._bandwidth_history.cache_clear()  # noqa: SLF001
    yield
    engine.get_breakout_state_store.cache_clear()
    engine._indicator_states.cache_clear()  # noqa: SLF001
    engine._last_indicator_snapshot.cache_clear()  # noqa: SLF001
    engine._last_seen_candle_ts.cache_clear()  # noqa: SLF001
    engine._bandwidth_history.cache_clear()  # noqa: SLF001


@pytest.fixture(autouse=True)
def _no_postgres(monkeypatch):
    """Nothing in this test file should ever touch a real Postgres
    connection — MarketState is empty for an unseeded symbol, so
    `_candles_for` would otherwise fall through to `fetch_candle_history`."""

    async def _empty_history(symbol: str, timeframe: str):
        return []

    monkeypatch.setattr(engine, "fetch_candle_history", _empty_history)


@pytest.mark.usefixtures("fake_redis")
async def test_scan_symbol_confirms_pdh_breakout_after_second_cycle(monkeypatch):
    symbol = "RELIANCE"
    await set_json(f"price:{symbol}", {"ltp": 2510.0, "volume": 100000})

    from app.services.redis_cache import hset_dict

    await hset_dict(indicator_key(symbol, "1d"), {"prev_high": "2500.0", "prev_low": "2400.0"})

    recorded_events = []
    notified_alerts = []

    async def _fake_record_breakout_event(signal):
        recorded_events.append(signal)

    async def _fake_active_alerts(symbol_arg):
        return [_FakeAlert(id=uuid.uuid4())]

    async def _fake_publish_alert_trigger(alert_id, signal):
        notified_alerts.append((alert_id, signal))

    async def _fake_record_alert_history(alert_id, signal):
        pass

    monkeypatch.setattr(engine, "record_breakout_event", _fake_record_breakout_event)
    monkeypatch.setattr(engine, "_active_alerts_for_symbol", _fake_active_alerts)
    monkeypatch.setattr(engine, "publish_alert_trigger", _fake_publish_alert_trigger)
    monkeypatch.setattr(engine, "record_alert_history", _fake_record_alert_history)

    cycle1 = datetime(2026, 9, 15, 10, 0, tzinfo=IST)
    monkeypatch.setattr(engine, "now_ist", lambda: cycle1)

    await engine._scan_symbol(symbol)  # noqa: SLF001

    store = engine.get_breakout_state_store()
    bullish_tracker = store.get_or_create(
        symbol, TriggerType.PDH_PDL, Direction.BULLISH, engine.DEFAULT_CONFIGS[TriggerType.PDH_PDL],
    )
    assert bullish_tracker.status is BreakoutStatus.TRIGGERED
    assert recorded_events == []  # not confirmed yet — first cross only

    # Advance past a 5-min confirmation-timeframe boundary, price still holding above PDH.
    cycle2 = cycle1 + timedelta(minutes=5)
    monkeypatch.setattr(engine, "now_ist", lambda: cycle2)

    await engine._scan_symbol(symbol)  # noqa: SLF001

    assert bullish_tracker.status is BreakoutStatus.CONFIRMED
    assert len(recorded_events) == 1
    confirmed_signal = recorded_events[0]
    assert confirmed_signal.symbol == symbol
    assert confirmed_signal.trigger_type is TriggerType.PDH_PDL
    assert confirmed_signal.direction is Direction.BULLISH
    assert confirmed_signal.score is not None  # scoring applied before persistence
    assert len(notified_alerts) == 1


@pytest.mark.usefixtures("fake_redis")
async def test_scan_symbol_no_op_when_no_price_data():
    # No price:{symbol} key seeded at all — must return cleanly, no crash.
    await engine._scan_symbol("NONEXISTENT")  # noqa: SLF001
    assert engine.get_breakout_state_store().all_active() == []


@pytest.mark.usefixtures("fake_redis")
async def test_scan_symbol_ignores_price_data_with_unparseable_ltp():
    await set_json("price:BADDATA", {"ltp": "not-a-number", "volume": 100})
    await engine._scan_symbol("BADDATA")  # noqa: SLF001
    assert engine.get_breakout_state_store().all_active() == []
