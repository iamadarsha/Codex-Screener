"""Pure candlestick pattern truth tables — synthetic data only, no mocks.

Mirrors `test_breakout_detectors.py`'s convention: plain pytest, Decimal
inputs via small local builder helpers, one `Test<ThingName>` class per
detector.
"""

from __future__ import annotations

from decimal import Decimal

from app.patterns.candlestick import (
    _engulfing_confidence,
    _harami_confidence,
    _hammer_confidence,
    _doji_confidence,
    _is_doji,
    _is_engulfing_bearish,
    _is_engulfing_bullish,
    _is_evening_star,
    _is_hammer,
    _is_harami_bearish,
    _is_harami_bullish,
    _is_morning_star,
    _is_three_black_crows,
    _is_three_white_soldiers,
    detect_candlestick_patterns,
)
from app.patterns.types import PatternDirection


def _ohlc(open_, high, low, close, volume=1000) -> dict:
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume}


class TestDoji:
    def test_small_body_is_doji_with_high_confidence(self):
        candle = _ohlc(100, 101, 99, 100.05)  # body=0.05, range=2, ratio=0.025
        assert _is_doji(candle) is True
        assert _doji_confidence(candle) == 0.75

    def test_large_body_is_not_doji(self):
        candle = _ohlc(100, 102, 99, 101)  # body=1, range=3, ratio=0.333
        assert _is_doji(candle) is False

    def test_zero_range_is_doji_with_full_confidence(self):
        candle = _ohlc(100, 100, 100, 100)
        assert _is_doji(candle) is True
        assert _doji_confidence(candle) == 1.0


class TestHammer:
    def test_long_lower_shadow_small_upper_is_hammer(self):
        candle = _ohlc(100, 101.5, 95, 101)  # body=1, lower=5, upper=0.5
        assert _is_hammer(candle) is True
        assert _hammer_confidence(candle) > 0.5

    def test_short_lower_shadow_is_not_hammer(self):
        candle = _ohlc(100, 105, 99.5, 101)  # lower=0.5, body=1 -> lower<2*body
        assert _is_hammer(candle) is False

    def test_zero_body_is_not_hammer(self):
        candle = _ohlc(100, 105, 95, 100)
        assert _is_hammer(candle) is False


class TestEngulfing:
    def test_bullish_engulfing_detected(self):
        prev = _ohlc(100, 101, 94, 95)  # bearish, body=5
        curr = _ohlc(94, 102, 93, 101)  # bullish, body=7, engulfs prev
        assert _is_engulfing_bullish(prev, curr) is True
        assert 0.0 < _engulfing_confidence(prev, curr) <= 1.0

    def test_bullish_engulfing_not_detected_when_open_too_high(self):
        prev = _ohlc(100, 101, 94, 95)
        curr = _ohlc(96, 102, 93, 101)  # open above prev close -> no engulf
        assert _is_engulfing_bullish(prev, curr) is False

    def test_bearish_engulfing_detected(self):
        prev = _ohlc(90, 96, 89, 95)  # bullish, body=5
        curr = _ohlc(96, 97, 88, 89)  # bearish, body=7, engulfs prev
        assert _is_engulfing_bearish(prev, curr) is True

    def test_bearish_engulfing_not_detected_when_close_too_high(self):
        prev = _ohlc(90, 96, 89, 95)
        curr = _ohlc(96, 97, 88, 94)  # close above prev open -> no engulf
        assert _is_engulfing_bearish(prev, curr) is False


class TestHarami:
    def test_bullish_harami_detected(self):
        prev = _ohlc(100, 101, 89, 90)  # bearish, body=10
        curr = _ohlc(92, 95.5, 91.5, 95)  # bullish, small body contained
        assert _is_harami_bullish(prev, curr) is True
        assert 0.0 <= _harami_confidence(prev, curr) <= 1.0

    def test_bullish_harami_not_detected_when_close_breaks_out(self):
        prev = _ohlc(100, 101, 89, 90)
        curr = _ohlc(92, 105, 91.5, 101)  # closes above prev open
        assert _is_harami_bullish(prev, curr) is False

    def test_bearish_harami_detected(self):
        prev = _ohlc(90, 101, 89, 100)  # bullish, body=10
        curr = _ohlc(98, 98.5, 94.5, 95)  # bearish, small body contained
        assert _is_harami_bearish(prev, curr) is True

    def test_bearish_harami_not_detected_when_close_breaks_out(self):
        prev = _ohlc(90, 101, 89, 100)
        curr = _ohlc(98, 98.5, 84, 85)  # closes below prev open
        assert _is_harami_bearish(prev, curr) is False


class TestStarPatterns:
    def test_morning_star_detected(self):
        c1 = _ohlc(100, 102, 89, 90)  # bearish, body=10
        c2 = _ohlc(89, 90, 88, 89.5)  # small body=0.5 < 0.3*10
        c3 = _ohlc(90, 98, 89, 97)  # bullish, closes above midpoint (95)
        assert _is_morning_star(c1, c2, c3) is True

    def test_morning_star_not_detected_when_close_below_midpoint(self):
        c1 = _ohlc(100, 102, 89, 90)
        c2 = _ohlc(89, 90, 88, 89.5)
        c3 = _ohlc(90, 94, 89, 93)  # closes below midpoint (95)
        assert _is_morning_star(c1, c2, c3) is False

    def test_evening_star_detected(self):
        c1 = _ohlc(90, 101, 89, 100)  # bullish, body=10
        c2 = _ohlc(100, 101, 99.5, 100.5)  # small body=0.5 < 0.3*10
        c3 = _ohlc(100, 101, 92, 93)  # bearish, closes below midpoint (95)
        assert _is_evening_star(c1, c2, c3) is True

    def test_evening_star_not_detected_when_close_above_midpoint(self):
        c1 = _ohlc(90, 101, 89, 100)
        c2 = _ohlc(100, 101, 99.5, 100.5)
        c3 = _ohlc(100, 101, 96, 97)  # closes above midpoint (95)
        assert _is_evening_star(c1, c2, c3) is False


class TestThreeSoldiersCrows:
    def test_three_white_soldiers_detected(self):
        c1 = _ohlc(90, 96, 89, 95)
        c2 = _ohlc(92, 100, 91, 99)
        c3 = _ohlc(94, 104, 93, 103)
        assert _is_three_white_soldiers(c1, c2, c3) is True

    def test_three_white_soldiers_not_detected_when_open_decreases(self):
        c1 = _ohlc(90, 96, 89, 95)
        c2 = _ohlc(92, 100, 91, 99)
        c3 = _ohlc(91, 104, 90, 103)  # open below c2's open
        assert _is_three_white_soldiers(c1, c2, c3) is False

    def test_three_black_crows_detected(self):
        c1 = _ohlc(96, 97, 90, 91)
        c2 = _ohlc(94, 95, 86, 87)
        c3 = _ohlc(92, 93, 82, 83)
        assert _is_three_black_crows(c1, c2, c3) is True

    def test_three_black_crows_not_detected_when_close_increases(self):
        c1 = _ohlc(96, 97, 90, 91)
        c2 = _ohlc(94, 95, 86, 87)
        c3 = _ohlc(92, 93, 88, 89)  # close above c2's close
        assert _is_three_black_crows(c1, c2, c3) is False


class TestDetectCandlestickPatterns:
    def test_empty_candles_returns_empty_list(self):
        assert detect_candlestick_patterns([]) == []

    def test_single_doji_candle_detected_via_public_api(self):
        candles = [_ohlc(100, 101, 99, 100.05)]
        matches = detect_candlestick_patterns(candles)
        names = [m.name for m in matches]
        assert "doji" in names
        doji = next(m for m in matches if m.name == "doji")
        assert doji.direction is PatternDirection.NEUTRAL
        assert 0.0 <= doji.confidence <= 1.0

    def test_three_candle_series_detects_morning_star_with_support(self):
        candles = [
            _ohlc(100, 102, 89, 90),
            _ohlc(89, 90, 88, 89.5),
            _ohlc(90, 98, 89, 97),
        ]
        matches = detect_candlestick_patterns(candles)
        star = next((m for m in matches if m.name == "morning_star"), None)
        assert star is not None
        assert star.direction is PatternDirection.BULLISH
        assert star.support == Decimal("88")
        assert 0.0 <= star.confidence <= 1.0

    def test_no_patterns_returns_empty_list(self):
        # A plain, unremarkable single candle: body too large for a doji,
        # lower shadow too short for a hammer.
        candles = [_ohlc(100, 108, 92, 105)]
        matches = detect_candlestick_patterns(candles)
        assert matches == []
