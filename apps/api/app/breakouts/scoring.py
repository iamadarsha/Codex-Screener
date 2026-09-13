"""Breakout DNA scoring — the full multi-factor, transparent scoring engine.

Replaces the old `compute_basic_score()` placeholder (volume-ratio +
level-distance only) with a six-component score that also reads trend
structure, momentum, volatility regime, and confirmation speed from the
per-symbol `SymbolIndicatorState` that `app.breakouts.engine` already holds
at signal time. Every component is independently visible on `DnaScore` —
the label (`overall`) is never the whole story, same "transparent scoring"
convention as `BreakoutSignal` itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.breakouts.detectors import bollinger_bandwidth
from app.breakouts.state_machine import DEFAULT_CONFIGS
from app.breakouts.types import BreakoutSignal, Direction
from app.market.indicators import SymbolIndicatorState

# ---------------------------------------------------------------------------
# Component weights (0-100 overall) — named constants, not magic numbers,
# summing to 100. Volume + level-distance keep the same relative 60/40 split
# `compute_basic_score` used, just rescaled to leave room for the four new
# components.
# ---------------------------------------------------------------------------
VOLUME_WEIGHT: float = 25.0
LEVEL_DISTANCE_WEIGHT: float = 15.0
TREND_ALIGNMENT_WEIGHT: float = 20.0
MOMENTUM_WEIGHT: float = 15.0
VOLATILITY_REGIME_WEIGHT: float = 15.0
CONFIRMATION_SPEED_WEIGHT: float = 10.0

# ---------------------------------------------------------------------------
# Sub-range thresholds
# ---------------------------------------------------------------------------
VOLUME_RATIO_CEILING: float = 3.0  # matches compute_basic_score's original clamp
LEVEL_DISTANCE_CEILING_PCT: float = 3.0  # matches compute_basic_score's original clamp

# RSI is read as momentum strength, not raw overbought/oversold: bullish
# breakouts are rewarded for RSI climbing away from the 50 midline, but the
# reward is capped at RSI_BULLISH_CEILING — extreme overbought readings
# beyond that don't score any higher than the ceiling itself. Bearish is the
# mirror image around the same midline.
RSI_MIDLINE: float = 50.0
RSI_BULLISH_CEILING: float = 85.0
RSI_BEARISH_FLOOR: float = 15.0

# Bollinger bandwidth read as a volatility-regime proxy: a narrow band (a
# squeeze that's now releasing) reads as a healthier breakout setup than one
# already happening inside a very wide, extended band. WIDE_BANDWIDTH_CAP is
# the bandwidth (as a fraction of the mid price) at/above which the regime
# is scored as fully "already extended" (fraction 0); 0 bandwidth scores as
# fraction 1. This is a single-reading proxy (no historical squeeze-then-
# expansion tracking here — that lives in `detectors.is_bollinger_squeeze`'s
# rolling-history version, not reachable from this pure signal+state
# signature), deliberately simple in the same spirit as the score it replaces.
WIDE_BANDWIDTH_CAP: float = 0.10

# Confirmation-speed reward decays linearly from full credit at an
# instant confirmation to zero credit at DOUBLE the trigger's own expected
# confirmation window (confirmation_bars * bar-length-in-minutes) — so a
# breakout that takes exactly as long as expected still earns half credit,
# and one that takes materially longer trails off toward zero.
CONFIRMATION_SPEED_ZERO_MULTIPLE: float = 2.0

_TIMEFRAME_MINUTES: dict[str, int] = {"1min": 1, "5min": 5, "15min": 15, "1d": 1440}


@dataclass(frozen=True, slots=True)
class DnaScore:
    """A breakout's full "DNA" score: an overall 0-100 read plus each named
    component that fed into it, independently inspectable."""

    overall: float
    volume: float
    level_distance: float
    trend_alignment: float
    momentum: float
    volatility_regime: float
    confirmation_speed: float


def _clamp01(fraction: float) -> float:
    return max(0.0, min(1.0, fraction))


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _volume_component(volume_ratio: float | None) -> float:
    fraction = _clamp01((volume_ratio or 0.0) / VOLUME_RATIO_CEILING)
    return fraction * VOLUME_WEIGHT


def _level_distance_component(reference_level: Decimal, trigger_price: Decimal) -> float:
    if not reference_level:
        return 0.0
    distance_pct = abs(float(trigger_price - reference_level) / float(reference_level)) * 100.0
    fraction = _clamp01(distance_pct / LEVEL_DISTANCE_CEILING_PCT)
    return fraction * LEVEL_DISTANCE_WEIGHT


def _trend_alignment_component(
    direction: Direction, price: Decimal, indicator_state: SymbolIndicatorState,
) -> float:
    """Score higher the more of {EMA9 vs EMA21, SMA50 vs SMA200, price vs
    EMA9, price vs SMA50} agree with the breakout's direction — a fully
    stacked bullish (or bearish) trend structure scores the full weight; no
    available MA data scores 0 rather than guessing."""
    price_f = float(price)
    ema_9 = indicator_state.ema_9.value
    ema_21 = indicator_state.ema_21.value
    sma_50 = indicator_state.sma_50.value
    sma_200 = indicator_state.sma_200.value

    checks: list[tuple[float | None, float | None]] = [
        (ema_9, ema_21),
        (sma_50, sma_200),
        (price_f, ema_9),
        (price_f, sma_50),
    ]
    applicable = [(short, long) for short, long in checks if short is not None and long is not None]
    if not applicable:
        return 0.0

    if direction is Direction.BULLISH:
        agreements = sum(1 for short, long in applicable if short > long)
    else:
        agreements = sum(1 for short, long in applicable if short < long)

    fraction = agreements / len(applicable)
    return fraction * TREND_ALIGNMENT_WEIGHT


def _momentum_component(direction: Direction, indicator_state: SymbolIndicatorState) -> float:
    rsi = indicator_state.rsi_14.value
    if rsi is None:
        return 0.0
    if direction is Direction.BULLISH:
        effective_rsi = min(rsi, RSI_BULLISH_CEILING)
        fraction = _clamp01((effective_rsi - RSI_MIDLINE) / (RSI_BULLISH_CEILING - RSI_MIDLINE))
    else:
        effective_rsi = max(rsi, RSI_BEARISH_FLOOR)
        fraction = _clamp01((RSI_MIDLINE - effective_rsi) / (RSI_MIDLINE - RSI_BEARISH_FLOOR))
    return fraction * MOMENTUM_WEIGHT


def _volatility_regime_component(indicator_state: SymbolIndicatorState) -> float:
    bandwidth = bollinger_bandwidth(
        _to_decimal(indicator_state.bollinger.upper),
        _to_decimal(indicator_state.bollinger.lower),
        _to_decimal(indicator_state.bollinger.mid),
    )
    if bandwidth is None:
        return 0.5 * VOLATILITY_REGIME_WEIGHT  # no reading yet — neutral, not penalized
    fraction = _clamp01(1.0 - (bandwidth / WIDE_BANDWIDTH_CAP))
    return fraction * VOLATILITY_REGIME_WEIGHT


def _confirmation_speed_component(signal: BreakoutSignal) -> float:
    if signal.triggered_at is None or signal.confirmed_at is None:
        return 0.0
    config = DEFAULT_CONFIGS.get(signal.trigger_type)
    if config is None:
        return 0.0
    minutes_per_bar = _TIMEFRAME_MINUTES.get(config.confirmation_timeframe, 5)
    expected_minutes = minutes_per_bar * config.confirmation_bars
    if expected_minutes <= 0:
        return 0.0
    actual_minutes = (signal.confirmed_at - signal.triggered_at).total_seconds() / 60.0
    zero_at_minutes = expected_minutes * CONFIRMATION_SPEED_ZERO_MULTIPLE
    fraction = _clamp01(1.0 - (actual_minutes / zero_at_minutes))
    return fraction * CONFIRMATION_SPEED_WEIGHT


def compute_dna_score(signal: BreakoutSignal, indicator_state: SymbolIndicatorState) -> DnaScore:
    """Compute the full Breakout DNA score for *signal*, using *indicator_state*
    (the same per-symbol `SymbolIndicatorState` `app.breakouts.engine` already
    maintains) for the trend/momentum/volatility-regime components."""
    price = signal.confirmation_price if signal.confirmation_price is not None else signal.trigger_price

    volume = round(_volume_component(signal.volume_ratio), 1)
    level_distance = round(_level_distance_component(signal.reference_level, signal.trigger_price), 1)
    trend_alignment = round(_trend_alignment_component(signal.direction, price, indicator_state), 1)
    momentum = round(_momentum_component(signal.direction, indicator_state), 1)
    volatility_regime = round(_volatility_regime_component(indicator_state), 1)
    confirmation_speed = round(_confirmation_speed_component(signal), 1)

    overall = round(
        volume + level_distance + trend_alignment + momentum + volatility_regime + confirmation_speed, 1,
    )

    return DnaScore(
        overall=overall,
        volume=volume,
        level_distance=level_distance,
        trend_alignment=trend_alignment,
        momentum=momentum,
        volatility_regime=volatility_regime,
        confirmation_speed=confirmation_speed,
    )
