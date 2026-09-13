"""Breakout FSM transitions — fully testable without live market data
(Milestone 3.2 acceptance gate), mirroring test_failover.py's style."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.breakouts.state_machine import BreakoutStateStore, BreakoutTracker, TriggerConfig
from app.breakouts.types import BreakoutStatus, Direction, ExpiryPolicy, RawEvent, TriggerType
from app.utils.time import IST

EOD_CONFIG = TriggerConfig(confirmation_bars=1, confirmation_timeframe="5min", expiry=ExpiryPolicy.END_OF_DAY)
ROLLING_CONFIG = TriggerConfig(
    confirmation_bars=2, confirmation_timeframe="15min", expiry=ExpiryPolicy.ROLLING_BARS, expiry_bars=2,
)

_NOW = datetime(2026, 9, 15, 10, 0, tzinfo=IST)


def _tracker(config: TriggerConfig = EOD_CONFIG) -> BreakoutTracker:
    return BreakoutTracker(symbol="RELIANCE", trigger_type=TriggerType.PDH_PDL, direction=Direction.BULLISH, config=config)


def test_armed_stays_armed_on_no_event():
    t = _tracker()
    signal = t.evaluate(RawEvent.NONE, Decimal(100), Decimal(95), _NOW, "bar1")
    assert signal is None
    assert t.status is BreakoutStatus.ARMED


def test_cross_up_moves_armed_to_triggered_without_emitting():
    t = _tracker()
    signal = t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")
    assert signal is None  # first cross is recorded, not yet alertable
    assert t.status is BreakoutStatus.TRIGGERED
    assert t.triggered_at == _NOW


def test_triggered_confirms_after_hold_on_a_new_bar():
    t = _tracker()  # confirmation_bars=1
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    later = _NOW + timedelta(minutes=5)
    signal = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(102), later, "bar2")

    assert signal is not None
    assert signal.status is BreakoutStatus.CONFIRMED
    assert signal.symbol == "RELIANCE"
    assert signal.reference_level == Decimal(100)
    assert signal.trigger_price == Decimal(102)
    assert signal.confirmation_price == Decimal(102)
    assert t.status is BreakoutStatus.CONFIRMED


def test_hold_on_the_same_bar_does_not_advance_confirmation():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")
    # Same bar_ts as the trigger — must not count as a confirmation bar.
    signal = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(101.5), _NOW, "bar1")
    assert signal is None
    assert t.status is BreakoutStatus.TRIGGERED
    assert t.bars_confirmed == 0


def test_multi_bar_confirmation_requires_n_distinct_hold_bars():
    t = _tracker(ROLLING_CONFIG)  # confirmation_bars=2
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    bar2 = _NOW + timedelta(minutes=15)
    signal1 = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(102), bar2, "bar2")
    assert signal1 is None  # only 1 of 2 required bars confirmed
    assert t.status is BreakoutStatus.TRIGGERED

    bar3 = bar2 + timedelta(minutes=15)
    signal2 = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(103), bar3, "bar3")
    assert signal2 is not None
    assert signal2.status is BreakoutStatus.CONFIRMED
    assert signal2.bars_confirmed == 2


def test_reverse_before_confirming_invalidates():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    later = _NOW + timedelta(minutes=5)
    signal = t.evaluate(RawEvent.REVERSE, Decimal(100), Decimal(98), later, "bar2")

    assert signal is not None
    assert signal.status is BreakoutStatus.INVALIDATED
    assert t.status is BreakoutStatus.INVALIDATED


def test_invalidated_can_re_trigger_on_a_later_cross():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")
    t.evaluate(RawEvent.REVERSE, Decimal(100), Decimal(98), _NOW + timedelta(minutes=5), "bar2")
    assert t.status is BreakoutStatus.INVALIDATED

    signal = t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW + timedelta(minutes=10), "bar3")
    assert signal is None
    assert t.status is BreakoutStatus.TRIGGERED


def test_confirmed_reverses_back_to_armed_not_invalidated():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")
    t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(102), _NOW + timedelta(minutes=5), "bar2")
    assert t.status is BreakoutStatus.CONFIRMED

    signal = t.evaluate(RawEvent.REVERSE, Decimal(100), Decimal(97), _NOW + timedelta(minutes=10), "bar3")
    assert signal is None  # re-arming isn't itself alertable
    assert t.status is BreakoutStatus.ARMED
    assert t.bars_confirmed == 0


def test_confirmed_stays_confirmed_on_continued_hold_no_refire():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")
    t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(102), _NOW + timedelta(minutes=5), "bar2")
    assert t.status is BreakoutStatus.CONFIRMED

    signal = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(103), _NOW + timedelta(minutes=10), "bar3")
    assert signal is None
    assert t.status is BreakoutStatus.CONFIRMED


def test_end_of_day_expiry_fires_when_market_closes_before_confirming():
    t = _tracker()
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    # Same calendar day as _NOW (2026-09-15), but past the 15:30 IST close —
    # derived from the injected `now`, never the real system clock's date.
    after_close = _NOW.replace(hour=15, minute=35)

    signal = t.evaluate(RawEvent.HOLD, Decimal(100), Decimal(102), after_close, "bar2")
    assert signal is not None
    assert signal.status is BreakoutStatus.EXPIRED
    assert t.status is BreakoutStatus.EXPIRED


def test_rolling_bars_expiry_fires_after_n_bars_with_zero_confirmations():
    t = _tracker(ROLLING_CONFIG)  # expiry_bars=2, confirmation_timeframe=15min
    t.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    # 2 bars x 15min = 30min with no HOLD ever recorded (event=NONE each time)
    still_watching = t.evaluate(RawEvent.NONE, Decimal(100), Decimal(99), _NOW + timedelta(minutes=20), "barX")
    assert still_watching is None

    expired = t.evaluate(RawEvent.NONE, Decimal(100), Decimal(99), _NOW + timedelta(minutes=40), "barY")
    assert expired is not None
    assert expired.status is BreakoutStatus.EXPIRED


def test_state_store_get_or_create_returns_same_tracker_for_same_key():
    store = BreakoutStateStore()
    t1 = store.get_or_create("TCS", TriggerType.ORB, Direction.BULLISH, EOD_CONFIG)
    t2 = store.get_or_create("TCS", TriggerType.ORB, Direction.BULLISH, EOD_CONFIG)
    assert t1 is t2


def test_state_store_distinguishes_direction_and_trigger_type():
    store = BreakoutStateStore()
    bullish = store.get_or_create("TCS", TriggerType.ORB, Direction.BULLISH, EOD_CONFIG)
    bearish = store.get_or_create("TCS", TriggerType.ORB, Direction.BEARISH, EOD_CONFIG)
    other_trigger = store.get_or_create("TCS", TriggerType.PDH_PDL, Direction.BULLISH, EOD_CONFIG)
    assert bullish is not bearish
    assert bullish is not other_trigger


def test_state_store_all_active_only_includes_triggered_and_confirmed():
    store = BreakoutStateStore()
    armed = store.get_or_create("TCS", TriggerType.ORB, Direction.BULLISH, EOD_CONFIG)
    triggered = store.get_or_create("INFY", TriggerType.ORB, Direction.BULLISH, EOD_CONFIG)
    triggered.evaluate(RawEvent.CROSS_UP, Decimal(100), Decimal(101), _NOW, "bar1")

    active = store.all_active()
    assert triggered in active
    assert armed not in active


def test_state_store_purge_expired_drops_stale_armed_trackers():
    store = BreakoutStateStore()
    tracker = store.get_or_create("WIPRO", TriggerType.PDH_PDL, Direction.BULLISH, EOD_CONFIG)
    tracker.last_updated = _NOW - timedelta(hours=48)

    removed = store.purge_expired(_NOW)
    assert removed == 1
    # A fresh get_or_create after purge creates a brand-new tracker instance.
    new_tracker = store.get_or_create("WIPRO", TriggerType.PDH_PDL, Direction.BULLISH, EOD_CONFIG)
    assert new_tracker is not tracker
