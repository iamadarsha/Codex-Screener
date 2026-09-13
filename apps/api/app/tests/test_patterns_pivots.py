"""Pure pivot-detection truth tables — synthetic data only, no mocks."""

from __future__ import annotations

import pytest

from app.patterns.pivots import find_pivots, pivot_highs, pivot_lows
from app.patterns.types import PivotKind


def _c(high, low) -> dict:
    return {"high": high, "low": low}


class TestFindPivots:
    def test_single_high_and_low_pivot_detected(self):
        candles = [
            _c(95, 90),  # idx0 context
            _c(110, 70),  # idx1 pivot high + pivot low
            _c(95, 90),  # idx2 valley (not a pivot)
            _c(105, 80),  # idx3 not a pivot high (105<110), not a pivot low (80>70)
        ]
        pivots = find_pivots(candles, window=1)
        highs = pivot_highs(pivots)
        lows = pivot_lows(pivots)
        assert len(highs) == 1
        assert highs[0].index == 1
        assert highs[0].price == 110
        assert len(lows) == 1
        assert lows[0].index == 1
        assert lows[0].price == 70

    def test_two_high_pivots_and_two_low_pivots(self):
        candles = [
            _c(95, 100),
            _c(110, 70),  # idx1: pivot high(110) + pivot low(70)
            _c(95, 90),
            _c(110, 80),  # idx3: pivot high(110) + pivot low(80)
            _c(95, 100),
        ]
        pivots = find_pivots(candles, window=1)
        highs = pivot_highs(pivots)
        lows = pivot_lows(pivots)
        assert [p.index for p in highs] == [1, 3]
        assert [p.index for p in lows] == [1, 3]

    def test_flat_series_has_no_pivots(self):
        candles = [_c(100, 90) for _ in range(5)]
        pivots = find_pivots(candles, window=1)
        assert pivots == []

    def test_insufficient_candles_returns_empty_list(self):
        # window=3 needs at least 2*3+1=7 candles.
        candles = [_c(100, 90) for _ in range(4)]
        assert find_pivots(candles, window=3) == []

    def test_window_less_than_one_raises(self):
        with pytest.raises(ValueError):
            find_pivots([_c(100, 90)], window=0)

    def test_pivot_kind_is_correctly_tagged(self):
        candles = [
            _c(95, 100),
            _c(110, 70),
            _c(95, 90),
        ]
        pivots = find_pivots(candles, window=1)
        kinds = {p.kind for p in pivots}
        assert kinds == {PivotKind.HIGH, PivotKind.LOW}
