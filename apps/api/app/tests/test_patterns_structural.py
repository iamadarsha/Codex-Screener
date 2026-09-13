"""Structural (multi-bar geometry) pattern truth tables — synthetic data
only, no mocks. Mirrors `test_breakout_detectors.py`'s convention.

Pivot-based detectors (triangle, double top/bottom, head & shoulders) are
exercised with `window=1` so the synthetic candle lists stay small; the
geometry checks themselves are unaffected by the window size.
"""

from __future__ import annotations

from app.patterns.structural import (
    detect_cup_and_handle,
    detect_darvas_box,
    detect_double_bottom,
    detect_double_top,
    detect_flag,
    detect_head_and_shoulders,
    detect_inverse_head_and_shoulders,
    detect_structural_patterns,
    detect_triangle,
)
from app.patterns.types import PatternDirection


def _c(high, low) -> dict:
    """Pivot-only candle: open/close are irrelevant to pivot-based detectors."""
    return {"open": (high + low) / 2, "high": high, "low": low, "close": (high + low) / 2}


def _ohlc(open_, high, low, close, volume=1000) -> dict:
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume}


class TestTriangle:
    def test_ascending_triangle_detected(self):
        candles = [
            _c(95, 90),
            _c(110, 70),  # pivot high #1 (flat resistance), pivot low #1
            _c(95, 90),
            _c(110, 80),  # pivot high #2 (flat resistance), pivot low #2 (rising)
            _c(95, 90),
        ]
        match = detect_triangle(candles, window=1)
        assert match is not None
        assert match.name == "ascending_triangle"
        assert match.direction is PatternDirection.BULLISH
        assert match.support == 80
        assert match.resistance == 110
        assert 0.0 <= match.confidence <= 1.0

    def test_descending_triangle_detected(self):
        candles = [
            _c(90, 80),
            _c(110, 70),  # pivot high #1, pivot low #1 (flat support)
            _c(90, 80),
            _c(100, 70),  # pivot high #2 (falling), pivot low #2 (flat support)
            _c(90, 80),
        ]
        match = detect_triangle(candles, window=1)
        assert match is not None
        assert match.name == "descending_triangle"
        assert match.direction is PatternDirection.BEARISH
        assert match.support == 70
        assert match.resistance == 100

    def test_symmetrical_triangle_detected(self):
        candles = [
            _c(90, 80),
            _c(110, 70),  # pivot high #1, pivot low #1
            _c(90, 85),
            _c(100, 80),  # pivot high #2 (falling), pivot low #2 (rising)
            _c(90, 85),
        ]
        match = detect_triangle(candles, window=1)
        assert match is not None
        assert match.name == "symmetrical_triangle"
        assert match.direction is PatternDirection.NEUTRAL

    def test_flat_parallel_channel_is_not_a_triangle(self):
        candles = [
            _c(95, 90),
            _c(110, 70),
            _c(95, 90),
            _c(110, 70),  # identical to pivot #1 -> both slopes flat, no convergence
            _c(95, 90),
        ]
        assert detect_triangle(candles, window=1) is None

    def test_insufficient_pivots_returns_none(self):
        candles = [_c(100, 90) for _ in range(5)]
        assert detect_triangle(candles, window=1) is None


class TestFlag:
    def test_bullish_flag_detected_after_sharp_pole(self):
        pole = [
            _ohlc(100, 100.2, 99.8, 100),
            _ohlc(100, 102.2, 99.8, 102),
            _ohlc(102, 104.2, 101.8, 104),
            _ohlc(104, 106.2, 103.8, 106),
            _ohlc(106, 108.2, 105.8, 108),
        ]
        flag = [
            _ohlc(108, 108.5, 107.5, 108.2),
            _ohlc(108.2, 108.7, 107.4, 107.8),
            _ohlc(107.8, 108.3, 107.3, 108.0),
            _ohlc(108.0, 108.6, 107.5, 107.9),
            _ohlc(107.9, 108.4, 107.4, 108.1),
        ]
        match = detect_flag(pole + flag, pole_len=5, flag_len=5)
        assert match is not None
        assert match.name == "flag"
        assert match.direction is PatternDirection.BULLISH
        assert float(match.support) == 107.3
        assert float(match.resistance) == 108.7
        assert 0.0 <= match.confidence <= 1.0

    def test_wide_consolidation_is_not_a_tight_flag(self):
        pole = [
            _ohlc(100, 100.2, 99.8, 100),
            _ohlc(100, 102.2, 99.8, 102),
            _ohlc(102, 104.2, 101.8, 104),
            _ohlc(104, 106.2, 103.8, 106),
            _ohlc(106, 108.2, 105.8, 108),
        ]
        wide = [
            _ohlc(108, 115, 100, 110),
            _ohlc(110, 116, 101, 105),
            _ohlc(105, 114, 100, 112),
            _ohlc(112, 117, 99, 103),
            _ohlc(103, 113, 98, 109),
        ]
        assert detect_flag(pole + wide, pole_len=5, flag_len=5) is None

    def test_choppy_pole_has_no_directional_conviction(self):
        choppy_pole = [
            _ohlc(100, 105, 95, 102),
            _ohlc(102, 106, 96, 99),
            _ohlc(99, 104, 94, 101),
            _ohlc(101, 105, 95, 98),
            _ohlc(98, 103, 93, 100),
        ]
        flag = [
            _ohlc(100, 100.5, 99.5, 100.2),
            _ohlc(100.2, 100.7, 99.4, 99.8),
            _ohlc(99.8, 100.3, 99.3, 100.0),
            _ohlc(100.0, 100.6, 99.5, 99.9),
            _ohlc(99.9, 100.4, 99.4, 100.1),
        ]
        assert detect_flag(choppy_pole + flag, pole_len=5, flag_len=5) is None


class TestDoubleTop:
    def test_double_top_detected(self):
        candles = [
            _c(90, 85),
            _c(100, 95),  # pivot high #1 (left top)
            _c(92, 90),  # pivot low between (trough)
            _c(100.5, 95),  # pivot high #2 (right top)
            _c(90, 85),
        ]
        match = detect_double_top(candles, window=1)
        assert match is not None
        assert match.name == "double_top"
        assert match.direction is PatternDirection.BEARISH
        assert match.support == 90
        assert 0.0 <= match.confidence <= 1.0

    def test_insufficient_pivot_highs_returns_none(self):
        candles = [_c(100, 90) for _ in range(5)]
        assert detect_double_top(candles, window=1) is None


class TestDoubleBottom:
    def test_double_bottom_detected(self):
        candles = [
            _c(110, 100),
            _c(105, 90),  # pivot low #1 (left bottom)
            _c(112, 105),  # pivot high between (peak)
            _c(105.5, 89.5),  # pivot low #2 (right bottom)
            _c(110, 100),
        ]
        match = detect_double_bottom(candles, window=1)
        assert match is not None
        assert match.name == "double_bottom"
        assert match.direction is PatternDirection.BULLISH
        assert match.resistance == 112
        assert 0.0 <= match.confidence <= 1.0

    def test_insufficient_pivot_lows_returns_none(self):
        candles = [_c(100, 90) for _ in range(5)]
        assert detect_double_bottom(candles, window=1) is None


class TestHeadAndShoulders:
    def test_head_and_shoulders_detected(self):
        candles = [
            _c(90, 80),  # idx0 context
            _c(100, 90),  # idx1 left shoulder
            _c(92, 85),  # idx2 valley
            _c(110, 95),  # idx3 head (highest)
            _c(92, 85),  # idx4 valley
            _c(100.5, 90),  # idx5 right shoulder
            _c(90, 80),  # idx6 context
        ]
        match = detect_head_and_shoulders(candles, window=1)
        assert match is not None
        assert match.name == "head_and_shoulders"
        assert match.direction is PatternDirection.BEARISH
        assert match.resistance == 110
        assert match.support == 85
        assert 0.0 <= match.confidence <= 1.0

    def test_asymmetric_shoulders_returns_none(self):
        candles = [
            _c(90, 80),
            _c(100, 90),  # left shoulder = 100
            _c(92, 85),
            _c(110, 95),  # head
            _c(92, 85),
            _c(130, 90),  # right shoulder way higher than left -> not comparable
            _c(90, 80),
        ]
        assert detect_head_and_shoulders(candles, window=1) is None


class TestInverseHeadAndShoulders:
    def test_inverse_head_and_shoulders_detected(self):
        candles = [
            _c(105, 100),  # idx0 context
            _c(92, 90),  # idx1 left shoulder low
            _c(98, 92),  # idx2 peak
            _c(90, 80),  # idx3 head (lowest)
            _c(98, 92),  # idx4 peak
            _c(92, 90.5),  # idx5 right shoulder low
            _c(105, 100),  # idx6 context
        ]
        match = detect_inverse_head_and_shoulders(candles, window=1)
        assert match is not None
        assert match.name == "inverse_head_and_shoulders"
        assert match.direction is PatternDirection.BULLISH
        assert match.support == 80
        assert match.resistance == 98
        assert 0.0 <= match.confidence <= 1.0

    def test_insufficient_pivot_lows_returns_none(self):
        candles = [_c(100, 90) for _ in range(5)]
        assert detect_inverse_head_and_shoulders(candles, window=1) is None


class TestCupAndHandle:
    @staticmethod
    def _cup_candles(rim: float = 105.0) -> list[dict]:
        # A smooth parabolic U from `rim` down to `rim - 25` and back up,
        # 15 bars, bottom sitting exactly in the middle (index 7 of 0..14).
        candles = []
        for i in range(15):
            factor = 1 - ((i - 7) ** 2) / 49
            low = 100 - 20 * factor
            high = low + 5 if i not in (0, 14) else rim
            candles.append(_ohlc(low, high, low, low))
        return candles

    def test_cup_and_handle_detected(self):
        cup = self._cup_candles()
        handle = [
            _ohlc(104, 105, 101, 103),
            _ohlc(103, 104.5, 101.5, 102.5),
            _ohlc(102.5, 104, 101, 103.5),
            _ohlc(103.5, 104.8, 101.2, 102.8),
            _ohlc(102.8, 104.2, 101.5, 103.9),
        ]
        match = detect_cup_and_handle(cup + handle, cup_len=15, handle_len=5)
        assert match is not None
        assert match.name == "cup_and_handle"
        assert match.direction is PatternDirection.BULLISH
        assert match.support == 80
        assert 0.0 <= match.confidence <= 1.0

    def test_mismatched_rims_returns_none(self):
        cup = self._cup_candles(rim=105.0)
        cup[-1] = _ohlc(100, 130, 100, 100)  # right rim far above left rim
        handle = [
            _ohlc(104, 105, 101, 103),
            _ohlc(103, 104.5, 101.5, 102.5),
            _ohlc(102.5, 104, 101, 103.5),
            _ohlc(103.5, 104.8, 101.2, 102.8),
            _ohlc(102.8, 104.2, 101.5, 103.9),
        ]
        assert detect_cup_and_handle(cup + handle, cup_len=15, handle_len=5) is None


class TestDarvasBox:
    @staticmethod
    def _box_candles(n: int = 10) -> list[dict]:
        return [_ohlc(102.5, 105, 100, 102.5) for _ in range(n)]

    def test_darvas_box_breakout_detected(self):
        box = self._box_candles()
        breakout = _ohlc(105, 111, 104, 110)
        match = detect_darvas_box(box + [breakout], box_len=10)
        assert match is not None
        assert match.name == "darvas_box"
        assert match.direction is PatternDirection.BULLISH
        assert match.support == 100
        assert match.resistance == 105
        assert 0.0 <= match.confidence <= 1.0

    def test_no_breakout_still_inside_box_returns_none(self):
        box = self._box_candles()
        still_inside = _ohlc(102, 104, 101, 103)
        assert detect_darvas_box(box + [still_inside], box_len=10) is None

    def test_wide_range_is_not_a_tight_box(self):
        wide_box = [_ohlc(102.5, 130, 80, 102.5) for _ in range(10)]
        breakout = _ohlc(130, 140, 129, 135)
        assert detect_darvas_box(wide_box + [breakout], box_len=10) is None


class TestDetectStructuralPatterns:
    def test_empty_candles_returns_empty_list(self):
        assert detect_structural_patterns([]) == []

    def test_darvas_only_series_returns_single_match(self):
        box = TestDarvasBox._box_candles()
        breakout = _ohlc(105, 111, 104, 110)
        matches = detect_structural_patterns(box + [breakout])
        assert len(matches) == 1
        assert matches[0].name == "darvas_box"
