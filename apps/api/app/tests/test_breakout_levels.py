"""Per-trigger-type reference-level computation — synthetic data only.

`orb_levels()` is the one impure function in `levels.py` (it reuses
`ORBDetector`'s Redis-backed storage) and is covered separately in
`test_breakout_engine.py` with the `fake_redis` fixture.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.breakouts.levels import (
    DEFAULT_DONCHIAN_LENGTH,
    donchian_levels,
    ema_cross_reference,
    fifty_two_week_levels,
    inside_bar_levels,
    macd_cross_reference,
    nr_levels,
    pdh_pdl_levels,
    volume_breakout_level,
    vwap_levels,
)
from app.breakouts.types import Direction, TriggerType


def _candle(high, low, close=None, open_=None, volume=1000):
    return {"high": high, "low": low, "close": close or high, "open": open_ or low, "volume": volume}


def test_pdh_pdl_levels_from_daily_indicator_hash():
    levels = pdh_pdl_levels({"prev_high": "2550.0", "prev_low": "2480.0"})
    assert len(levels) == 2
    bullish = next(l for l in levels if l.direction is Direction.BULLISH)
    bearish = next(l for l in levels if l.direction is Direction.BEARISH)
    assert bullish.level == Decimal("2550.0")
    assert bearish.level == Decimal("2480.0")
    assert all(l.trigger_type is TriggerType.PDH_PDL for l in levels)


def test_pdh_pdl_missing_fields_produce_no_levels():
    assert pdh_pdl_levels({}) == []


def test_fifty_two_week_levels_use_ind_1d_not_intraday_state():
    levels = fifty_two_week_levels({"high_52w": "3000.0", "low_52w": "1800.0"})
    assert len(levels) == 2
    assert {l.direction for l in levels} == {Direction.BULLISH, Direction.BEARISH}
    assert all(l.trigger_type is TriggerType.FIFTY_TWO_WEEK for l in levels)


def test_fifty_two_week_missing_low_only_returns_high():
    levels = fifty_two_week_levels({"high_52w": "3000.0"})
    assert len(levels) == 1
    assert levels[0].direction is Direction.BULLISH


def test_donchian_levels_over_window():
    candles = [_candle(100 + i, 90 + i) for i in range(DEFAULT_DONCHIAN_LENGTH)]
    levels = donchian_levels(candles)
    assert len(levels) == 2
    bullish = next(l for l in levels if l.direction is Direction.BULLISH)
    bearish = next(l for l in levels if l.direction is Direction.BEARISH)
    assert bullish.level == Decimal(str(100 + DEFAULT_DONCHIAN_LENGTH - 1))
    assert bearish.level == Decimal(str(90))


def test_donchian_insufficient_history_returns_empty():
    candles = [_candle(100, 90) for _ in range(5)]
    assert donchian_levels(candles, length=20) == []


def test_nr4_levels_bilateral_at_narrowest_bar():
    candles = [_candle(110, 90), _candle(108, 95), _candle(105, 96), _candle(101, 99)]
    levels = nr_levels(candles, 4)
    assert len(levels) == 2
    assert all(l.trigger_type is TriggerType.NR4 for l in levels)
    bullish = next(l for l in levels if l.direction is Direction.BULLISH)
    bearish = next(l for l in levels if l.direction is Direction.BEARISH)
    assert bullish.level == Decimal("101")
    assert bearish.level == Decimal("99")


def test_nr7_uses_nr7_trigger_type():
    candles = [_candle(120 - i, 80 + i) for i in range(6)] + [_candle(101, 99)]
    levels = nr_levels(candles, 7)
    assert levels and all(l.trigger_type is TriggerType.NR7 for l in levels)


def test_nr4_no_setup_when_last_bar_not_narrowest():
    candles = [_candle(101, 100), _candle(108, 95), _candle(105, 96), _candle(110, 90)]
    assert nr_levels(candles, 4) == []


def test_inside_bar_levels_at_contained_bars_own_range():
    candles = [_candle(110, 90), _candle(105, 95)]
    levels = inside_bar_levels(candles)
    assert len(levels) == 2
    bullish = next(l for l in levels if l.direction is Direction.BULLISH)
    bearish = next(l for l in levels if l.direction is Direction.BEARISH)
    assert bullish.level == Decimal("105")
    assert bearish.level == Decimal("95")


def test_inside_bar_no_setup_when_not_contained():
    candles = [_candle(110, 90), _candle(111, 95)]
    assert inside_bar_levels(candles) == []


def test_volume_breakout_level_uses_multiplier():
    level = volume_breakout_level({"sma_20_volume": "100000"}, multiplier=2.0)
    assert level is not None
    assert level.level == Decimal("200000.0")
    assert level.direction is Direction.BULLISH
    assert level.trigger_type is TriggerType.VOLUME_BREAKOUT


def test_volume_breakout_level_none_without_avg_volume():
    assert volume_breakout_level({}) is None


def test_vwap_levels_bilateral_same_value():
    levels = vwap_levels({"vwap": "2500.5"})
    assert len(levels) == 2
    assert {l.direction for l in levels} == {Direction.BULLISH, Direction.BEARISH}
    assert all(l.level == Decimal("2500.5") for l in levels)


def test_vwap_levels_empty_without_vwap():
    assert vwap_levels({}) == []


def test_ema_and_macd_cross_reference_values():
    assert ema_cross_reference({"ema_21": "150.25"}) == Decimal("150.25")
    assert macd_cross_reference({"macd_signal": "0.42"}) == Decimal("0.42")


@pytest.mark.parametrize("fn", [ema_cross_reference, macd_cross_reference])
def test_cross_reference_none_when_missing(fn):
    assert fn({}) is None
