"""Pure classifier/pattern-detection truth tables — synthetic data only."""

from __future__ import annotations

from decimal import Decimal

from app.breakouts.detectors import (
    bollinger_bandwidth,
    classify_event,
    classify_series_cross,
    is_bollinger_squeeze,
    is_inside_bar,
    narrowest_range_bar,
)
from app.breakouts.types import Direction, RawEvent


def _c(high: float, low: float) -> dict:
    return {"high": high, "low": low}


class TestClassifyEvent:
    def test_bullish_cross_up_from_below(self):
        event = classify_event(Direction.BULLISH, Decimal(100), Decimal(99), Decimal(101), was_triggered=False)
        assert event is RawEvent.CROSS_UP

    def test_bearish_cross_down_from_above(self):
        event = classify_event(Direction.BEARISH, Decimal(100), Decimal(101), Decimal(99), was_triggered=False)
        assert event is RawEvent.CROSS_DOWN

    def test_no_prior_value_but_already_beyond_level_still_crosses(self):
        # First-ever observation, already past the level (e.g. a gap-up
        # past PDH before the engine's cold start caught up) — must not be
        # silently missed just because there's no "was below" data point.
        event = classify_event(Direction.BULLISH, Decimal(100), None, Decimal(101), was_triggered=False)
        assert event is RawEvent.CROSS_UP

    def test_no_prior_value_and_not_beyond_level_is_none(self):
        event = classify_event(Direction.BULLISH, Decimal(100), None, Decimal(95), was_triggered=False)
        assert event is RawEvent.NONE

    def test_not_yet_triggered_and_not_crossing_is_none(self):
        event = classify_event(Direction.BULLISH, Decimal(100), Decimal(95), Decimal(96), was_triggered=False)
        assert event is RawEvent.NONE

    def test_triggered_and_still_holding_bullish(self):
        event = classify_event(Direction.BULLISH, Decimal(100), Decimal(101), Decimal(102), was_triggered=True)
        assert event is RawEvent.HOLD

    def test_triggered_and_still_holding_bearish(self):
        event = classify_event(Direction.BEARISH, Decimal(100), Decimal(99), Decimal(98), was_triggered=True)
        assert event is RawEvent.HOLD

    def test_triggered_bullish_reverses_back_below_level(self):
        event = classify_event(Direction.BULLISH, Decimal(100), Decimal(101), Decimal(99), was_triggered=True)
        assert event is RawEvent.REVERSE

    def test_triggered_bearish_reverses_back_above_level(self):
        event = classify_event(Direction.BEARISH, Decimal(100), Decimal(99), Decimal(101), was_triggered=True)
        assert event is RawEvent.REVERSE

    def test_zero_level_zero_crossing_diff_is_cross_up(self):
        # The EMA/MACD-cross "diff vs zero" trick used in engine.py.
        event = classify_event(Direction.BULLISH, Decimal(0), Decimal("-0.5"), Decimal("0.5"), was_triggered=False)
        assert event is RawEvent.CROSS_UP


class TestClassifySeriesCross:
    def test_bullish_cross(self):
        assert classify_series_cross(Decimal(10), Decimal(11), Decimal(12), Decimal(11)) is RawEvent.CROSS_UP

    def test_bearish_cross(self):
        assert classify_series_cross(Decimal(12), Decimal(11), Decimal(10), Decimal(11)) is RawEvent.CROSS_DOWN

    def test_no_cross_when_order_unchanged(self):
        assert classify_series_cross(Decimal(12), Decimal(10), Decimal(13), Decimal(10)) is RawEvent.NONE

    def test_missing_values_are_none(self):
        assert classify_series_cross(None, Decimal(1), Decimal(1), Decimal(1)) is RawEvent.NONE


class TestNarrowestRangeBar:
    def test_last_bar_narrowest_of_four_is_nr4(self):
        candles = [_c(110, 90), _c(108, 95), _c(105, 96), _c(101, 99)]  # last range=2, others wider
        bar = narrowest_range_bar(candles, 4)
        assert bar == candles[-1]

    def test_last_bar_not_narrowest_returns_none(self):
        candles = [_c(101, 100), _c(108, 95), _c(105, 96), _c(110, 90)]  # last range=10, widest
        assert narrowest_range_bar(candles, 4) is None

    def test_insufficient_history_returns_none(self):
        assert narrowest_range_bar([_c(101, 100)], 4) is None


class TestInsideBar:
    def test_contained_bar_is_inside(self):
        prev = _c(110, 90)
        current = _c(105, 95)
        assert is_inside_bar(prev, current) is True

    def test_bar_breaking_high_is_not_inside(self):
        prev = _c(110, 90)
        current = _c(111, 95)
        assert is_inside_bar(prev, current) is False

    def test_bar_breaking_low_is_not_inside(self):
        prev = _c(110, 90)
        current = _c(105, 89)
        assert is_inside_bar(prev, current) is False

    def test_exact_containment_boundary_counts_as_inside(self):
        prev = _c(110, 90)
        current = _c(110, 90)
        assert is_inside_bar(prev, current) is True


class TestBollingerSqueeze:
    def test_bandwidth_computation(self):
        bw = bollinger_bandwidth(Decimal(110), Decimal(90), Decimal(100))
        assert bw == 0.2

    def test_bandwidth_none_when_mid_zero(self):
        assert bollinger_bandwidth(Decimal(110), Decimal(90), Decimal(0)) is None

    def test_squeeze_true_when_bandwidth_in_bottom_20_percent(self):
        history = [0.5, 0.4, 0.3, 0.2, 0.1, 0.05]
        assert is_bollinger_squeeze(history, 0.05) is True

    def test_squeeze_false_when_bandwidth_is_wide(self):
        history = [0.5, 0.4, 0.3, 0.2, 0.1, 0.05]
        assert is_bollinger_squeeze(history, 0.5) is False

    def test_squeeze_false_with_insufficient_history(self):
        assert is_bollinger_squeeze([0.1, 0.2], 0.05) is False

    def test_squeeze_false_when_bandwidth_is_none(self):
        assert is_bollinger_squeeze([0.1, 0.2, 0.3, 0.4, 0.5], None) is False
