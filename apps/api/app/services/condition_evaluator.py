"""Evaluate scan conditions against symbol indicator data."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Union

import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported indicator names (must match Redis hash field names)
# ---------------------------------------------------------------------------
INDICATOR_NAMES: frozenset[str] = frozenset(
    {
        "close",
        "open",
        "high",
        "low",
        "ema_9",
        "ema_21",
        "rsi_14",
        "sma_20",
        "sma_50",
        "sma_200",
        "vwap",
        "volume",
        "macd",
        "macd_signal",
        "atr_14",
        "bollinger_upper",
        "bollinger_lower",
        "bollinger_mid",
    }
)


# ---------------------------------------------------------------------------
# Operator enum
# ---------------------------------------------------------------------------
class ConditionOperator(str, enum.Enum):
    """Comparison operators supported by the scan engine."""

    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    EQUALS = "equals"
    INCREASING = "increasing"
    DECREASING = "decreasing"


# ---------------------------------------------------------------------------
# Operand dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class IndicatorRef:
    """Reference to an indicator value for a symbol.

    Parameters
    ----------
    name:
        Indicator field name (e.g. ``"rsi_14"``, ``"close"``).
    timeframe:
        Candle timeframe – ``"1d"``, ``"15min"`` etc.  Defaults to ``"1d"``.
    lookback:
        Number of historical periods to consider (used by cross / trend
        operators).  ``0`` means the *current* value.
    """

    name: str = ""
    timeframe: str = "1d"
    lookback: int = 0


@dataclass(frozen=True, slots=True)
class NumericLiteral:
    """A fixed numeric value used as an operand."""

    value: Decimal = field(default_factory=lambda: Decimal(0))


# Convenience type alias
Operand = Union[IndicatorRef, NumericLiteral, Decimal, float, int]


# ---------------------------------------------------------------------------
# Condition dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Condition:
    """A single scan condition.

    *left* and *right* are operands – each can be an :class:`IndicatorRef`,
    a :class:`NumericLiteral`, or a plain number.

    For the ``BETWEEN`` operator *right* must be a **tuple** of two operands
    ``(low, high)``.

    For ``INCREASING`` / ``DECREASING`` *right* is unused (may be ``None``).
    """

    left: Operand
    operator: ConditionOperator
    right: Operand | tuple[Operand, Operand] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_decimal(value: object) -> Decimal | None:
    """Coerce a value to :class:`Decimal`, returning ``None`` on failure."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _resolve_operand(
    operand: Operand,
    symbol_data: dict[str, str | None],
) -> Decimal | None:
    """Return the numeric value of *operand* given the symbol's indicator hash.

    For :class:`IndicatorRef` the value is looked up from *symbol_data* (a
    flat ``{field: value}`` dict that comes straight from the Redis hash).
    """
    if isinstance(operand, IndicatorRef):
        raw = symbol_data.get(operand.name)
        return _to_decimal(raw)
    if isinstance(operand, NumericLiteral):
        return operand.value
    # plain number
    return _to_decimal(operand)


def _resolve_prev_operand(
    operand: Operand,
    symbol_data: dict[str, str | None],
) -> Decimal | None:
    """Return the *previous* value of *operand*.

    The convention is that the previous tick's value is stored in
    ``symbol_data`` with a ``prev_`` prefix (e.g. ``prev_ema_9``).  If
    unavailable we return ``None`` and the cross-detection will be skipped.
    """
    if isinstance(operand, IndicatorRef):
        raw = symbol_data.get(f"prev_{operand.name}")
        return _to_decimal(raw)
    # literals have no "previous" – they are constant
    return _resolve_operand(operand, symbol_data)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_condition(
    condition: Condition,
    symbol_data: dict[str, str | None],
) -> bool:
    """Evaluate a single :class:`Condition` against *symbol_data*.

    Returns ``False`` when operands cannot be resolved (missing data).
    """
    op = condition.operator

    left_val = _resolve_operand(condition.left, symbol_data)
    if left_val is None:
        return False

    # ----- unary / self-referential operators -----
    if op is ConditionOperator.INCREASING:
        prev = _resolve_prev_operand(condition.left, symbol_data)
        return prev is not None and left_val > prev

    if op is ConditionOperator.DECREASING:
        prev = _resolve_prev_operand(condition.left, symbol_data)
        return prev is not None and left_val < prev

    # ----- BETWEEN requires a pair -----
    if op is ConditionOperator.BETWEEN:
        if not isinstance(condition.right, tuple) or len(condition.right) != 2:
            log.warning("between_missing_bounds", condition=condition)
            return False
        lo = _resolve_operand(condition.right[0], symbol_data)
        hi = _resolve_operand(condition.right[1], symbol_data)
        if lo is None or hi is None:
            return False
        return lo <= left_val <= hi

    # ----- binary operators -----
    right_val = _resolve_operand(condition.right, symbol_data)  # type: ignore[arg-type]
    if right_val is None:
        return False

    if op is ConditionOperator.GREATER_THAN:
        return left_val > right_val

    if op is ConditionOperator.LESS_THAN:
        return left_val < right_val

    if op is ConditionOperator.EQUALS:
        return left_val == right_val

    # ----- cross operators -----
    if op in (ConditionOperator.CROSSES_ABOVE, ConditionOperator.CROSSES_BELOW):
        prev_left = _resolve_prev_operand(condition.left, symbol_data)
        prev_right = _resolve_prev_operand(condition.right, symbol_data)  # type: ignore[arg-type]
        if prev_left is None or prev_right is None:
            return False
        if op is ConditionOperator.CROSSES_ABOVE:
            return prev_left <= prev_right and left_val > right_val
        # CROSSES_BELOW
        return prev_left >= prev_right and left_val < right_val

    log.warning("unsupported_operator", operator=op)
    return False


# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------

def evaluate_conditions(
    conditions: list[Condition],
    symbol_data: dict[str, str | None],
    logic: str = "AND",
) -> bool:
    """Evaluate a list of conditions combined with *logic* (``"AND"`` or ``"OR"``).

    Returns ``True`` when the overall expression is satisfied.
    """
    if not conditions:
        return False

    if logic.upper() == "OR":
        return any(evaluate_condition(c, symbol_data) for c in conditions)
    # default: AND
    return all(evaluate_condition(c, symbol_data) for c in conditions)
