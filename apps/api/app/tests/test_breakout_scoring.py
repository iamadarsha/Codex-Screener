"""Breakout DNA scoring truth tables — pure math over a `BreakoutSignal` +
`SymbolIndicatorState` constructed directly, no mocks (mirrors
`test_breakout_detectors.py`'s convention)."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.breakouts.scoring import (
    CONFIRMATION_SPEED_WEIGHT,
    LEVEL_DISTANCE_WEIGHT,
    MOMENTUM_WEIGHT,
    TREND_ALIGNMENT_WEIGHT,
    VOLATILITY_REGIME_WEIGHT,
    VOLUME_WEIGHT,
    compute_dna_score,
)
from app.breakouts.state_machine import DEFAULT_CONFIGS
from app.breakouts.types import BreakoutSignal, BreakoutStatus, Direction, TriggerType
from app.market.indicators import SymbolIndicatorState
from app.utils.time import IST

_NOW = datetime(2026, 9, 15, 10, 0, tzinfo=IST)


_UNSET = object()


def _signal(
    trigger_type: TriggerType = TriggerType.PDH_PDL,
    direction: Direction = Direction.BULLISH,
    status: BreakoutStatus = BreakoutStatus.CONFIRMED,
    reference_level: Decimal = Decimal(100),
    trigger_price: Decimal = Decimal(100),
    confirmation_price: Decimal | None = Decimal(100),
    volume_ratio: float | None = 1.5,
    triggered_at: datetime = _NOW,
    confirmed_at: object = _UNSET,
) -> BreakoutSignal:
    return BreakoutSignal(
        symbol="RELIANCE",
        trigger_type=trigger_type,
        direction=direction,
        status=status,
        reference_level=reference_level,
        trigger_price=trigger_price,
        confirmation_price=confirmation_price,
        triggered_at=triggered_at,
        confirmed_at=triggered_at if confirmed_at is _UNSET else confirmed_at,
        bars_confirmed=1,
        volume_ratio=volume_ratio,
    )


def _indicators(
    ema_9: float | None = None,
    ema_21: float | None = None,
    sma_50: float | None = None,
    sma_200: float | None = None,
    rsi_14: float | None = None,
    bollinger: tuple[float, float, float] | None = None,
) -> SymbolIndicatorState:
    state = SymbolIndicatorState()
    state.ema_9.value = ema_9
    state.ema_21.value = ema_21
    state.sma_50.value = sma_50
    state.sma_200.value = sma_200
    state.rsi_14.value = rsi_14
    if bollinger is not None:
        upper, mid, lower = bollinger
        state.bollinger.upper = upper
        state.bollinger.mid = mid
        state.bollinger.lower = lower
    return state


class TestVolumeComponent:
    def test_zero_volume_ratio_scores_zero(self):
        score = compute_dna_score(_signal(volume_ratio=0.0), _indicators())
        assert score.volume == 0.0

    def test_none_volume_ratio_treated_as_zero(self):
        score = compute_dna_score(_signal(volume_ratio=None), _indicators())
        assert score.volume == 0.0

    def test_volume_ratio_clamped_at_ceiling(self):
        at_ceiling = compute_dna_score(_signal(volume_ratio=3.0), _indicators())
        beyond_ceiling = compute_dna_score(_signal(volume_ratio=10.0), _indicators())
        assert at_ceiling.volume == beyond_ceiling.volume == VOLUME_WEIGHT

    def test_half_ratio_scores_half_weight(self):
        score = compute_dna_score(_signal(volume_ratio=1.5), _indicators())
        assert score.volume == round(VOLUME_WEIGHT / 2, 1)


class TestLevelDistanceComponent:
    def test_zero_distance_scores_zero(self):
        score = compute_dna_score(
            _signal(reference_level=Decimal(100), trigger_price=Decimal(100), volume_ratio=0.0), _indicators(),
        )
        assert score.level_distance == 0.0

    def test_distance_at_or_beyond_ceiling_clamps_at_full_weight(self):
        score = compute_dna_score(
            _signal(reference_level=Decimal(100), trigger_price=Decimal(110), volume_ratio=0.0), _indicators(),
        )
        assert score.level_distance == LEVEL_DISTANCE_WEIGHT

    def test_zero_reference_level_guard_no_division_error(self):
        score = compute_dna_score(
            _signal(reference_level=Decimal(0), trigger_price=Decimal(100), volume_ratio=0.0), _indicators(),
        )
        assert score.level_distance == 0.0


class TestTrendAlignmentComponent:
    def test_fully_stacked_bullish_trend_scores_full_weight(self):
        indicators = _indicators(ema_9=110, ema_21=105, sma_50=100, sma_200=90)
        score = compute_dna_score(
            _signal(direction=Direction.BULLISH, confirmation_price=Decimal(115), volume_ratio=0.0), indicators,
        )
        assert score.trend_alignment == TREND_ALIGNMENT_WEIGHT

    def test_fully_stacked_bearish_trend_scores_full_weight(self):
        indicators = _indicators(ema_9=90, ema_21=95, sma_50=100, sma_200=110)
        score = compute_dna_score(
            _signal(direction=Direction.BEARISH, confirmation_price=Decimal(85), volume_ratio=0.0), indicators,
        )
        assert score.trend_alignment == TREND_ALIGNMENT_WEIGHT

    def test_no_ma_agreement_scores_zero(self):
        # Every MA is stacked the *opposite* way of the bullish breakout.
        indicators = _indicators(ema_9=90, ema_21=95, sma_50=100, sma_200=110)
        score = compute_dna_score(
            _signal(direction=Direction.BULLISH, confirmation_price=Decimal(85), volume_ratio=0.0), indicators,
        )
        assert score.trend_alignment == 0.0

    def test_no_indicator_data_scores_zero_not_a_guess(self):
        score = compute_dna_score(_signal(volume_ratio=0.0), _indicators())
        assert score.trend_alignment == 0.0

    def test_partial_agreement_scores_partial_weight(self):
        # Only ema_9 > ema_21 agrees (bullish); sma_50 vs sma_200 disagrees,
        # price is below both ema_9 and sma_50.
        indicators = _indicators(ema_9=105, ema_21=100, sma_50=100, sma_200=110)
        score = compute_dna_score(
            _signal(direction=Direction.BULLISH, confirmation_price=Decimal(90), volume_ratio=0.0), indicators,
        )
        assert 0.0 < score.trend_alignment < TREND_ALIGNMENT_WEIGHT


class TestMomentumComponent:
    def test_bullish_at_midline_rsi_scores_zero(self):
        score = compute_dna_score(_signal(direction=Direction.BULLISH, volume_ratio=0.0), _indicators(rsi_14=50.0))
        assert score.momentum == 0.0

    def test_bullish_at_ceiling_rsi_scores_full_weight(self):
        score = compute_dna_score(_signal(direction=Direction.BULLISH, volume_ratio=0.0), _indicators(rsi_14=85.0))
        assert score.momentum == MOMENTUM_WEIGHT

    def test_bullish_extreme_overbought_not_rewarded_beyond_ceiling(self):
        at_ceiling = compute_dna_score(
            _signal(direction=Direction.BULLISH, volume_ratio=0.0), _indicators(rsi_14=85.0),
        )
        beyond_ceiling = compute_dna_score(
            _signal(direction=Direction.BULLISH, volume_ratio=0.0), _indicators(rsi_14=98.0),
        )
        assert at_ceiling.momentum == beyond_ceiling.momentum

    def test_bearish_at_midline_rsi_scores_zero(self):
        score = compute_dna_score(_signal(direction=Direction.BEARISH, volume_ratio=0.0), _indicators(rsi_14=50.0))
        assert score.momentum == 0.0

    def test_bearish_at_floor_rsi_scores_full_weight(self):
        score = compute_dna_score(_signal(direction=Direction.BEARISH, volume_ratio=0.0), _indicators(rsi_14=15.0))
        assert score.momentum == MOMENTUM_WEIGHT

    def test_bearish_extreme_oversold_not_rewarded_beyond_floor(self):
        at_floor = compute_dna_score(_signal(direction=Direction.BEARISH, volume_ratio=0.0), _indicators(rsi_14=15.0))
        beyond_floor = compute_dna_score(_signal(direction=Direction.BEARISH, volume_ratio=0.0), _indicators(rsi_14=2.0))
        assert at_floor.momentum == beyond_floor.momentum

    def test_missing_rsi_scores_zero(self):
        score = compute_dna_score(_signal(direction=Direction.BULLISH, volume_ratio=0.0), _indicators(rsi_14=None))
        assert score.momentum == 0.0


class TestVolatilityRegimeComponent:
    def test_zero_bandwidth_scores_full_weight(self):
        score = compute_dna_score(_signal(volume_ratio=0.0), _indicators(bollinger=(100.0, 100.0, 100.0)))
        assert score.volatility_regime == VOLATILITY_REGIME_WEIGHT

    def test_wide_bandwidth_at_or_beyond_cap_scores_zero(self):
        # bandwidth = (upper-lower)/mid = 20/100 = 0.20, well beyond the 0.10 cap
        score = compute_dna_score(_signal(volume_ratio=0.0), _indicators(bollinger=(110.0, 100.0, 90.0)))
        assert score.volatility_regime == 0.0

    def test_missing_bollinger_data_scores_neutral_half_weight(self):
        score = compute_dna_score(_signal(volume_ratio=0.0), _indicators())
        assert score.volatility_regime == round(VOLATILITY_REGIME_WEIGHT / 2, 1)


class TestConfirmationSpeedComponent:
    def test_instant_confirmation_scores_full_weight(self):
        signal = _signal(
            trigger_type=TriggerType.PDH_PDL, triggered_at=_NOW, confirmed_at=_NOW, volume_ratio=0.0,
        )
        score = compute_dna_score(signal, _indicators())
        assert score.confirmation_speed == CONFIRMATION_SPEED_WEIGHT

    def test_slow_confirmation_beyond_double_expected_scores_zero(self):
        config = DEFAULT_CONFIGS[TriggerType.PDH_PDL]
        expected_minutes = config.confirmation_bars * 5  # PDH_PDL uses 5min bars
        confirmed_at = _NOW + timedelta(minutes=expected_minutes * 3)
        signal = _signal(
            trigger_type=TriggerType.PDH_PDL, triggered_at=_NOW, confirmed_at=confirmed_at, volume_ratio=0.0,
        )
        score = compute_dna_score(signal, _indicators())
        assert score.confirmation_speed == 0.0

    def test_confirmation_at_exactly_expected_window_scores_half_weight(self):
        config = DEFAULT_CONFIGS[TriggerType.PDH_PDL]
        expected_minutes = config.confirmation_bars * 5
        confirmed_at = _NOW + timedelta(minutes=expected_minutes)
        signal = _signal(
            trigger_type=TriggerType.PDH_PDL, triggered_at=_NOW, confirmed_at=confirmed_at, volume_ratio=0.0,
        )
        score = compute_dna_score(signal, _indicators())
        assert score.confirmation_speed == round(CONFIRMATION_SPEED_WEIGHT / 2, 1)

    def test_missing_confirmed_at_scores_zero(self):
        signal = _signal(
            trigger_type=TriggerType.PDH_PDL, triggered_at=_NOW, confirmed_at=None, volume_ratio=0.0,
        )
        score = compute_dna_score(signal, _indicators())
        assert score.confirmation_speed == 0.0


class TestOverallScore:
    def test_overall_is_sum_of_all_components(self):
        indicators = _indicators(
            ema_9=110, ema_21=105, sma_50=100, sma_200=90, rsi_14=70.0, bollinger=(105.0, 100.0, 95.0),
        )
        signal = _signal(
            trigger_type=TriggerType.PDH_PDL,
            direction=Direction.BULLISH,
            reference_level=Decimal(100),
            trigger_price=Decimal(102),
            confirmation_price=Decimal(102),
            volume_ratio=1.5,
            triggered_at=_NOW,
            confirmed_at=_NOW + timedelta(minutes=5),
        )
        score = compute_dna_score(signal, indicators)
        expected = round(
            score.volume
            + score.level_distance
            + score.trend_alignment
            + score.momentum
            + score.volatility_regime
            + score.confirmation_speed,
            1,
        )
        assert score.overall == expected

    def test_overall_within_bounds(self):
        indicators = _indicators(
            ema_9=110, ema_21=105, sma_50=100, sma_200=90, rsi_14=70.0, bollinger=(105.0, 100.0, 95.0),
        )
        signal = _signal(volume_ratio=1.5, confirmed_at=_NOW + timedelta(minutes=5))
        score = compute_dna_score(signal, indicators)
        assert 0.0 <= score.overall <= 100.0

    def test_best_case_signal_scores_near_maximum(self):
        indicators = _indicators(
            ema_9=115, ema_21=105, sma_50=100, sma_200=90, rsi_14=85.0, bollinger=(100.0, 100.0, 100.0),
        )
        signal = _signal(
            direction=Direction.BULLISH,
            reference_level=Decimal(100),
            trigger_price=Decimal(110),
            confirmation_price=Decimal(120),  # above every MA, so all four trend checks agree
            volume_ratio=3.0,
            triggered_at=_NOW,
            confirmed_at=_NOW,
        )
        score = compute_dna_score(signal, indicators)
        assert score.overall == 100.0
