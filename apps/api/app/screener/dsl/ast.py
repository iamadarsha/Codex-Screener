"""AST for the scan expression language (master prompt §14-17).

Pure data — frozen dataclasses, no evaluation logic (see evaluator.py) and
no parsing logic (see parser.py). Additive to the existing
`app.services.condition_evaluator`, which keeps serving the 13 prebuilt
scans unchanged — see the Phase 3.1 plan for why.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Value-producing nodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PriceField:
    """A raw OHLCV field, optionally offset `offset` bars into the past
    (0 = current/most-recent bar). Replaces the dead `IndicatorRef.lookback`
    field in condition_evaluator.py with one that's actually read."""

    name: str  # "open" | "high" | "low" | "close" | "volume"
    offset: int = 0


@dataclass(frozen=True, slots=True)
class IndicatorCall:
    """A named indicator, optionally parameterized, optionally offset.

    `name` is looked up in the registry (registry.py) to decide whether it
    resolves from Phase 2's precomputed `ind:{symbol}:{tf}` hash or needs
    on-the-fly computation from raw candle history.
    """

    name: str  # e.g. "sma", "ema", "rsi", "macd", "atr", "bollinger_upper", "vwap"
    params: tuple[tuple[str, int], ...] = ()  # e.g. (("length", 20),) — sorted, hashable
    offset: int = 0

    def param(self, key: str, default: int | None = None) -> int | None:
        for k, v in self.params:
            if k == key:
                return v
        return default


@dataclass(frozen=True, slots=True)
class Literal:
    value: float


ValueNode = PriceField | IndicatorCall | Literal


# ---------------------------------------------------------------------------
# Rolling functions (master prompt §16)
# ---------------------------------------------------------------------------


class RollingFn(str, Enum):
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    HIGHEST = "highest"
    LOWEST = "lowest"


@dataclass(frozen=True, slots=True)
class RollingFunction:
    """A rolling aggregate over the last `n` bars of `expr`.

    `COUNT(predicate, n)` is the one exception where the aggregated thing is
    a boolean predicate rather than a numeric expr — `predicate` is set and
    `expr` is unused in that case.
    """

    fn: RollingFn
    n: int
    expr: ValueNode | None = None
    predicate: "Comparison | None" = None


AggregatableNode = ValueNode | RollingFunction

# ---------------------------------------------------------------------------
# Comparisons and crossovers
# ---------------------------------------------------------------------------


class CompareOp(str, Enum):
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


@dataclass(frozen=True, slots=True)
class Comparison:
    left: AggregatableNode
    op: CompareOp
    right: AggregatableNode


@dataclass(frozen=True, slots=True)
class CrossesAbove:
    """True iff `left` was <= `right` on the previous bar and is > `right`
    on the current bar — a real crossover, not a bare inequality (master
    prompt §14: "Do NOT confuse `A > B` with `A crossed above B`")."""

    left: ValueNode
    right: ValueNode


@dataclass(frozen=True, slots=True)
class CrossesBelow:
    left: ValueNode
    right: ValueNode


# ---------------------------------------------------------------------------
# Boolean groups (master prompt §17 — real nesting, unlike the flat-only
# `evaluate_conditions(conditions, logic="AND"|"OR")` in condition_evaluator.py)
# ---------------------------------------------------------------------------

BoolLeaf = Comparison | CrossesAbove | CrossesBelow


@dataclass(frozen=True, slots=True)
class BoolAnd:
    clauses: tuple["BoolNode", ...]


@dataclass(frozen=True, slots=True)
class BoolOr:
    clauses: tuple["BoolNode", ...]


@dataclass(frozen=True, slots=True)
class BoolNot:
    clause: "BoolNode"


BoolNode = BoolLeaf | BoolAnd | BoolOr | BoolNot
