"""Twelve prebuilt scan definitions shipped with BreakoutScan."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import structlog

from app.services.condition_evaluator import (
    Condition,
    ConditionOperator,
    IndicatorRef,
    NumericLiteral,
)

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Type alias for a full scan definition dict
# ---------------------------------------------------------------------------
ScanDefinition = dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ind(name: str, timeframe: str = "1d", lookback: int = 0) -> IndicatorRef:
    return IndicatorRef(name=name, timeframe=timeframe, lookback=lookback)


def _num(value: str | int | float) -> NumericLiteral:
    return NumericLiteral(value=Decimal(str(value)))


# ---------------------------------------------------------------------------
# Prebuilt scan catalogue
# ---------------------------------------------------------------------------

_PREBUILT_SCANS: list[ScanDefinition] = [
    # 1 ----------------------------------------------------------------
    {
        "id": "rsi_oversold",
        "name": "RSI Oversold",
        "description": "RSI(14) below 30 -- potential reversal candidates.",
        "conditions": [
            Condition(
                left=_ind("rsi_14"),
                operator=ConditionOperator.LESS_THAN,
                right=_num(30),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 2 ----------------------------------------------------------------
    {
        "id": "rsi_overbought",
        "name": "RSI Overbought",
        "description": "RSI(14) above 70 -- potentially overextended.",
        "conditions": [
            Condition(
                left=_ind("rsi_14"),
                operator=ConditionOperator.GREATER_THAN,
                right=_num(70),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 3 ----------------------------------------------------------------
    {
        "id": "bullish_ema_crossover",
        "name": "Bullish EMA Crossover",
        "description": "EMA(9) crosses above EMA(21) -- bullish momentum shift.",
        "conditions": [
            Condition(
                left=_ind("ema_9"),
                operator=ConditionOperator.CROSSES_ABOVE,
                right=_ind("ema_21"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 4 ----------------------------------------------------------------
    {
        "id": "bearish_ema_crossover",
        "name": "Bearish EMA Crossover",
        "description": "EMA(9) crosses below EMA(21) -- bearish momentum shift.",
        "conditions": [
            Condition(
                left=_ind("ema_9"),
                operator=ConditionOperator.CROSSES_BELOW,
                right=_ind("ema_21"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 5 ----------------------------------------------------------------
    {
        "id": "price_above_sma200",
        "name": "Price Above SMA(200)",
        "description": "Close price is above the 200-day SMA -- long-term uptrend.",
        "conditions": [
            Condition(
                left=_ind("close"),
                operator=ConditionOperator.GREATER_THAN,
                right=_ind("sma_200"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 6 ----------------------------------------------------------------
    {
        "id": "price_below_sma200",
        "name": "Price Below SMA(200)",
        "description": "Close price is below the 200-day SMA -- long-term downtrend.",
        "conditions": [
            Condition(
                left=_ind("close"),
                operator=ConditionOperator.LESS_THAN,
                right=_ind("sma_200"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 7 ----------------------------------------------------------------
    #   Volume spike:  volume > 2 * sma_20 (of volume).
    #   We represent the right-hand side as a *special* indicator
    #   "volume_sma_20" that the engine should pre-compute, OR we
    #   encode it as:  volume / sma_20_volume > 2.
    #   For simplicity the engine will inject a synthetic field
    #   "volume_sma_20" when preparing data.  The condition just
    #   compares volume > 2x that value.
    #   A pragmatic alternative: store the ratio in the hash or use
    #   two conditions (volume > 2 * volume_sma_20).
    #   Here we use a *custom* flag so the engine knows to handle it.
    {
        "id": "volume_spike",
        "name": "Volume Spike (2x)",
        "description": "Current volume is more than 2x the 20-period average volume.",
        "conditions": [
            Condition(
                left=_ind("volume"),
                operator=ConditionOperator.GREATER_THAN,
                right=_ind("volume_sma_20"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
        "meta": {"note": "Engine must provide volume_sma_20 = sma_20_volume * 2"},
    },
    # 8 ----------------------------------------------------------------
    #   Bollinger squeeze:  (BB_upper - BB_lower) / BB_mid < 0.04
    #   We encode this with a synthetic field "bollinger_width_pct"
    #   that the engine pre-computes.
    {
        "id": "bollinger_squeeze",
        "name": "Bollinger Squeeze",
        "description": "Bollinger bandwidth < 4 % -- volatility contraction.",
        "conditions": [
            Condition(
                left=_ind("bollinger_width_pct"),
                operator=ConditionOperator.LESS_THAN,
                right=_num("0.04"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
        "meta": {
            "note": "Engine must inject bollinger_width_pct = (bb_upper - bb_lower) / bb_mid",
        },
    },
    # 9 ----------------------------------------------------------------
    {
        "id": "macd_bullish_cross",
        "name": "MACD Bullish Cross",
        "description": "MACD line crosses above Signal line.",
        "conditions": [
            Condition(
                left=_ind("macd"),
                operator=ConditionOperator.CROSSES_ABOVE,
                right=_ind("macd_signal"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
    },
    # 10 ---------------------------------------------------------------
    #   Near 52-week high:  close > 0.95 * 52-week-high
    #   The engine should inject "high_52w" from its own data source;
    #   condition: close > high_52w_95 where high_52w_95 = 0.95 * high_52w
    {
        "id": "near_52_week_high",
        "name": "Near 52-Week High",
        "description": "Close is within 5 % of the 52-week high.",
        "conditions": [
            Condition(
                left=_ind("close"),
                operator=ConditionOperator.GREATER_THAN,
                right=_ind("high_52w_95"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "1d",
        "meta": {"note": "Engine must inject high_52w_95 = 0.95 * 52-week high"},
    },
    # 11 ---------------------------------------------------------------
    #   ORB breakout long:  close > orb_high
    {
        "id": "orb_breakout_long",
        "name": "ORB Breakout Long",
        "description": "Price above the Opening Range high (first 15 min).",
        "conditions": [
            Condition(
                left=_ind("close"),
                operator=ConditionOperator.GREATER_THAN,
                right=_ind("orb_high"),
            ),
        ],
        "universe": "nifty500",
        "timeframe": "15min",
        "meta": {"note": "Engine must inject orb_high from ORBDetector"},
    },
    # 12 ---------------------------------------------------------------
    #   Bullish engulfing uses pattern detection rather than a
    #   numeric condition.  We store a special flag so the engine
    #   calls the pattern detector.
    {
        "id": "bullish_engulfing",
        "name": "Bullish Engulfing",
        "description": "Bullish engulfing candlestick pattern detected.",
        "conditions": [],
        "universe": "nifty500",
        "timeframe": "1d",
        "pattern": "engulfing_bullish",
    },
]

# Build lookup index once at import time
_SCAN_INDEX: dict[str, ScanDefinition] = {s["id"]: s for s in _PREBUILT_SCANS}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_prebuilt_scans() -> list[ScanDefinition]:
    """Return all 12 prebuilt scan definitions."""
    return list(_PREBUILT_SCANS)


def get_scan_by_id(scan_id: str) -> ScanDefinition | None:
    """Return a single scan definition by its id, or ``None``."""
    return _SCAN_INDEX.get(scan_id)
