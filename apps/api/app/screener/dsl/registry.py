"""Indicator registry (master prompt's registry.py requirement).

Resolves a DSL `IndicatorCall` to either a precomputed Redis-hash field
(fast path — Phase 2's `app.market.indicators` already computes these) or
an on-the-fly incremental computation from raw candle history. Callers
(`parser.py`) must always pass fully-populated, key-sorted `params` tuples
(defaults merged in) so the equality checks here are exact and simple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.market import indicators as inc

Params = tuple[tuple[str, int], ...]


def param(params: Params, key: str, default: int) -> int:
    for k, v in params:
        if k == key:
            return v
    return default


def canonical_params(params: Params, defaults: Params) -> Params:
    """Merge `params` over `defaults` and return a key-sorted tuple."""
    merged = dict(defaults)
    merged.update(dict(params))
    return tuple(sorted(merged.items()))


@dataclass(frozen=True)
class IndicatorSpec:
    default_params: Params
    precomputed_field: Callable[[Params], str | None]
    """Given canonicalized params, return the precomputed hash field name
    if this exact parameterization matches Phase 2's indicator engine,
    else None (caller falls back to on-the-fly computation)."""
    make_state: Callable[[Params], object] | None
    """Factory for a fresh on-the-fly incremental state object (from
    app.market.indicators), or None if not implemented on the fly."""


def _sma_field(p: Params) -> str | None:
    return {20: "sma_20", 50: "sma_50", 200: "sma_200"}.get(param(p, "length", 20))


def _ema_field(p: Params) -> str | None:
    return {9: "ema_9", 21: "ema_21"}.get(param(p, "length", 9))


def _rsi_field(p: Params) -> str | None:
    return "rsi_14" if param(p, "length", 14) == 14 else None


def _atr_field(p: Params) -> str | None:
    return "atr_14" if param(p, "length", 14) == 14 else None


def _bb_field(field_name: str) -> Callable[[Params], str | None]:
    def _fn(p: Params) -> str | None:
        if param(p, "length", 20) == 20 and param(p, "std", 2) == 2:
            return field_name
        return None

    return _fn


def _macd_field(field_name: str) -> Callable[[Params], str | None]:
    def _fn(p: Params) -> str | None:
        if (
            param(p, "fast", 12) == 12
            and param(p, "slow", 26) == 26
            and param(p, "signal", 9) == 9
        ):
            return field_name
        return None

    return _fn


def _sma_volume_field(p: Params) -> str | None:
    return "sma_20_volume" if param(p, "length", 20) == 20 else None


REGISTRY: dict[str, IndicatorSpec] = {
    "sma": IndicatorSpec(
        (("length", 20),), _sma_field, lambda p: inc.SmaState(param(p, "length", 20))
    ),
    "ema": IndicatorSpec(
        (("length", 9),), _ema_field, lambda p: inc.EmaState(param(p, "length", 9))
    ),
    "rsi": IndicatorSpec(
        (("length", 14),), _rsi_field, lambda p: inc.RsiState(param(p, "length", 14))
    ),
    "atr": IndicatorSpec(
        (("length", 14),), _atr_field, lambda p: inc.AtrState(param(p, "length", 14))
    ),
    "vwap": IndicatorSpec((), lambda p: "vwap", None),  # always precomputed, session-scoped
    "bollinger_upper": IndicatorSpec(
        (("length", 20), ("std", 2)), _bb_field("bollinger_upper"), None
    ),
    "bollinger_mid": IndicatorSpec(
        (("length", 20), ("std", 2)), _bb_field("bollinger_mid"), None
    ),
    "bollinger_lower": IndicatorSpec(
        (("length", 20), ("std", 2)), _bb_field("bollinger_lower"), None
    ),
    "macd": IndicatorSpec(
        (("fast", 12), ("slow", 26), ("signal", 9)), _macd_field("macd"), None
    ),
    "macd_signal": IndicatorSpec(
        (("fast", 12), ("slow", 26), ("signal", 9)), _macd_field("macd_signal"), None
    ),
    "sma_volume": IndicatorSpec((("length", 20),), _sma_volume_field, None),
    "high_52w": IndicatorSpec((), lambda p: "high_52w", None),
    # Registered but not yet implemented (master prompt lists these as
    # required eventually) — honestly scoped rather than silently wrong.
    # Adding one later is a matter of writing its make_state factory, not
    # restructuring anything.
    "roc": IndicatorSpec((("length", 12),), lambda p: None, None),
    "cci": IndicatorSpec((("length", 20),), lambda p: None, None),
    "mfi": IndicatorSpec((("length", 14),), lambda p: None, None),
    "obv": IndicatorSpec((), lambda p: None, None),
    "stochastic": IndicatorSpec((("k", 14), ("d", 3)), lambda p: None, None),
    "williams_r": IndicatorSpec((("length", 14),), lambda p: None, None),
    "donchian": IndicatorSpec((("length", 20),), lambda p: None, None),
}

NOT_YET_IMPLEMENTED = frozenset(
    {"roc", "cci", "mfi", "obv", "stochastic", "williams_r", "donchian"}
)


def is_known_indicator(name: str) -> bool:
    return name in REGISTRY


def default_params(name: str) -> Params:
    spec = REGISTRY.get(name)
    return spec.default_params if spec else ()


def resolve_precomputed_field(name: str, params: Params) -> str | None:
    spec = REGISTRY.get(name)
    if spec is None:
        return None
    return spec.precomputed_field(params)


def make_incremental_state(name: str, params: Params):
    """Raises NotImplementedError for indicators with no on-the-fly path."""
    if name in NOT_YET_IMPLEMENTED:
        raise NotImplementedError(
            f"Indicator {name!r} is registered but has no on-the-fly implementation yet."
        )
    spec = REGISTRY.get(name)
    if spec is None or spec.make_state is None:
        raise NotImplementedError(
            f"Indicator {name!r} has no on-the-fly (non-precomputed) implementation."
        )
    return spec.make_state(params)
