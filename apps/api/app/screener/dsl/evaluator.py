"""Execute a validated DSL tree against one symbol's data.

Two data sources per symbol:
- `indicator_data`: the precomputed Redis-hash dict (`ind:{symbol}:{tf}`,
  the same shape `app.market.indicators.SymbolIndicatorState.update()`
  produces) — the fast path for offset=0 lookups of standard indicators.
- `candles`: a chronological list of OHLCV dicts (oldest first) — used for
  historical offsets, rolling functions, and on-the-fly indicator
  computation via `app.market.indicators`' incremental state classes
  (Phase 2), replayed across the buffer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.screener.dsl import registry
from app.screener.dsl.ast import (
    AggregatableNode,
    BoolAnd,
    BoolNode,
    BoolNot,
    BoolOr,
    Comparison,
    CompareOp,
    CrossesAbove,
    CrossesBelow,
    IndicatorCall,
    Literal,
    PriceField,
    RollingFn,
    RollingFunction,
    ValueNode,
)
from app.utils.decimals import safe_decimal


@dataclass
class EvalContext:
    indicator_data: dict[str, str | None]
    candles: list[dict[str, float]]  # chronological, oldest first
    _series_cache: dict[tuple, list[Decimal | None]] = field(default_factory=dict, repr=False)


def evaluate(root: BoolNode, ctx: EvalContext) -> bool:
    return _eval_bool(root, ctx)


def _eval_bool(node: BoolNode, ctx: EvalContext) -> bool:
    if isinstance(node, BoolAnd):
        return all(_eval_bool(c, ctx) for c in node.clauses)
    if isinstance(node, BoolOr):
        return any(_eval_bool(c, ctx) for c in node.clauses)
    if isinstance(node, BoolNot):
        return not _eval_bool(node.clause, ctx)
    if isinstance(node, Comparison):
        left = _eval_aggregatable(node.left, ctx)
        right = _eval_aggregatable(node.right, ctx)
        if left is None or right is None:
            return False
        return _compare(left, node.op, right)
    if isinstance(node, CrossesAbove):
        return _eval_cross(node.left, node.right, ctx, above=True)
    if isinstance(node, CrossesBelow):
        return _eval_cross(node.left, node.right, ctx, above=False)
    raise TypeError(f"unhandled bool node: {node!r}")


def _compare(left: Decimal, op: CompareOp, right: Decimal) -> bool:
    if op is CompareOp.GT:
        return left > right
    if op is CompareOp.LT:
        return left < right
    if op is CompareOp.GTE:
        return left >= right
    if op is CompareOp.LTE:
        return left <= right
    if op is CompareOp.EQ:
        return left == right
    if op is CompareOp.NEQ:
        return left != right
    raise TypeError(f"unhandled compare op: {op!r}")


def _operand_offset(node: ValueNode) -> int:
    return getattr(node, "offset", 0)


def _eval_cross(left: ValueNode, right: ValueNode, ctx: EvalContext, above: bool) -> bool:
    left_offset = _operand_offset(left)
    right_offset = _operand_offset(right)
    left_now = _eval_value(left, ctx, offset=left_offset)
    right_now = _eval_value(right, ctx, offset=right_offset)
    left_prev = _eval_value(left, ctx, offset=left_offset + 1)
    right_prev = _eval_value(right, ctx, offset=right_offset + 1)
    if None in (left_now, right_now, left_prev, right_prev):
        return False
    if above:
        return left_prev <= right_prev and left_now > right_now
    return left_prev >= right_prev and left_now < right_now


def _eval_aggregatable(node: AggregatableNode, ctx: EvalContext) -> Decimal | None:
    if isinstance(node, RollingFunction):
        return _eval_rolling(node, ctx)
    return _eval_value(node, ctx, offset=_operand_offset(node))


def _eval_value(node: ValueNode, ctx: EvalContext, offset: int) -> Decimal | None:
    if isinstance(node, Literal):
        return Decimal(str(node.value))
    if isinstance(node, PriceField):
        return _price_from_candles(ctx.candles, node.name, offset)
    if isinstance(node, IndicatorCall):
        return _indicator_value(node, ctx, offset)
    return None


def _price_from_candles(candles: list[dict], field_name: str, offset: int) -> Decimal | None:
    idx = len(candles) - 1 - offset
    if idx < 0 or idx >= len(candles):
        return None
    return safe_decimal(candles[idx].get(field_name))


def _indicator_value(node: IndicatorCall, ctx: EvalContext, offset: int) -> Decimal | None:
    if offset == 0:
        field_name = registry.resolve_precomputed_field(node.name, node.params)
        if field_name is not None:
            resolved = safe_decimal(ctx.indicator_data.get(field_name))
            if resolved is not None:
                return resolved
    # On-the-fly path: replay from candle history (cached per-evaluation so
    # repeated lookups of the same indicator don't replay redundantly).
    if not ctx.candles:
        return None
    series = _get_or_replay_series(node.name, node.params, ctx)
    idx = len(series) - 1 - offset
    if idx < 0 or idx >= len(series):
        return None
    return series[idx]


def _get_or_replay_series(
    name: str, params: tuple[tuple[str, int], ...], ctx: EvalContext
) -> list[Decimal | None]:
    cache_key = (name, params)
    cached = ctx._series_cache.get(cache_key)  # noqa: SLF001
    if cached is not None:
        return cached
    series = _replay_indicator_series(name, params, ctx.candles)
    ctx._series_cache[cache_key] = series  # noqa: SLF001
    return series


def _replay_indicator_series(
    name: str, params: tuple[tuple[str, int], ...], candles: list[dict]
) -> list[Decimal | None]:
    state = registry.make_incremental_state(name, params)
    series: list[Decimal | None] = []
    for c in candles:
        close = float(c.get("close", 0) or 0)
        if name == "atr":
            high = float(c.get("high", 0) or 0)
            low = float(c.get("low", 0) or 0)
            val = state.update(high, low, close)
        elif name == "sma_volume":
            vol = float(c.get("volume", 0) or 0)
            val = state.update(vol)
        else:
            val = state.update(close)
        series.append(Decimal(str(val)) if val is not None else None)
    return series


def _eval_rolling(node: RollingFunction, ctx: EvalContext) -> Decimal | None:
    if node.fn is RollingFn.COUNT:
        predicate = node.predicate
        if predicate is None:
            return None
        left_offset = _operand_offset(predicate.left)
        right_offset = _operand_offset(predicate.right)
        count = 0
        for i in range(node.n):
            left = _eval_value(predicate.left, ctx, offset=left_offset + i)
            right = _eval_value(predicate.right, ctx, offset=right_offset + i)
            if left is None or right is None:
                continue
            if _compare(left, predicate.op, right):
                count += 1
        return Decimal(count)

    if node.expr is None:
        return None
    expr_offset = _operand_offset(node.expr)
    values: list[Decimal] = []
    for i in range(node.n):
        v = _eval_value(node.expr, ctx, offset=expr_offset + i)
        if v is not None:
            values.append(v)
    if not values:
        return None

    if node.fn in (RollingFn.MIN, RollingFn.LOWEST):
        return min(values)
    if node.fn in (RollingFn.MAX, RollingFn.HIGHEST):
        return max(values)
    if node.fn is RollingFn.SUM:
        return sum(values)
    if node.fn is RollingFn.AVG:
        return sum(values) / len(values)
    raise TypeError(f"unhandled rolling fn: {node.fn!r}")
