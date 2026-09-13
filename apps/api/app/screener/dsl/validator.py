"""Validate a parsed DSL tree before it reaches the compiler (master prompt
§40: reject unknown indicators/fields, invalid timeframes, absurd
lookbacks, malformed combinations — before anything executes)."""

from __future__ import annotations

from app.screener.dsl import registry
from app.screener.dsl.ast import (
    BoolAnd,
    BoolNode,
    BoolNot,
    BoolOr,
    Comparison,
    CrossesAbove,
    CrossesBelow,
    IndicatorCall,
    Literal,
    PriceField,
    RollingFn,
    RollingFunction,
)

MAX_OFFSET = 500  # bars — generous for daily data, rejects clearly-absurd values
MAX_ROLLING_WINDOW = 500
MAX_TREE_DEPTH = 20
VALID_TIMEFRAMES = frozenset(
    {"1m", "2m", "3m", "5m", "10m", "15m", "30m", "60m", "1min", "5min", "15min", "1d", "1w", "1mo"}
)


class DslValidationError(ValueError):
    """Raised with every problem found, not just the first (better for a
    scan-builder UI to surface all issues at once)."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


def validate(root: BoolNode, timeframe: str = "1d") -> None:
    problems: list[str] = []

    if timeframe not in VALID_TIMEFRAMES:
        problems.append(f"invalid timeframe {timeframe!r}")

    _walk_bool(root, depth=0, problems=problems)

    if problems:
        raise DslValidationError(problems)


def _walk_bool(node: BoolNode, depth: int, problems: list[str]) -> None:
    if depth > MAX_TREE_DEPTH:
        problems.append(f"boolean nesting exceeds max depth {MAX_TREE_DEPTH}")
        return

    if isinstance(node, BoolAnd):
        if not node.clauses:
            problems.append("'and' group has no clauses")
        for c in node.clauses:
            _walk_bool(c, depth + 1, problems)
    elif isinstance(node, BoolOr):
        if not node.clauses:
            problems.append("'or' group has no clauses")
        for c in node.clauses:
            _walk_bool(c, depth + 1, problems)
    elif isinstance(node, BoolNot):
        _walk_bool(node.clause, depth + 1, problems)
    elif isinstance(node, Comparison):
        _walk_aggregatable(node.left, problems)
        _walk_aggregatable(node.right, problems)
    elif isinstance(node, (CrossesAbove, CrossesBelow)):
        _walk_value(node.left, problems)
        _walk_value(node.right, problems)
    else:
        problems.append(f"unrecognized bool node: {node!r}")


def _walk_aggregatable(node, problems: list[str]) -> None:
    if isinstance(node, RollingFunction):
        if not (1 <= node.n <= MAX_ROLLING_WINDOW):
            problems.append(
                f"rolling window n={node.n} out of range (1..{MAX_ROLLING_WINDOW})"
            )
        if node.fn is RollingFn.COUNT:
            if node.predicate is None:
                problems.append("COUNT rolling function requires a predicate")
            else:
                _walk_aggregatable(node.predicate.left, problems)
                _walk_aggregatable(node.predicate.right, problems)
        else:
            if node.expr is None:
                problems.append(f"rolling function {node.fn.value!r} requires an expression")
            else:
                _walk_value(node.expr, problems)
    else:
        _walk_value(node, problems)


def _walk_value(node, problems: list[str]) -> None:
    if isinstance(node, PriceField):
        if not (0 <= node.offset <= MAX_OFFSET):
            problems.append(f"offset {node.offset} out of range for field {node.name!r}")
    elif isinstance(node, IndicatorCall):
        if not registry.is_known_indicator(node.name):
            problems.append(f"unknown indicator {node.name!r}")
        elif node.name in registry.NOT_YET_IMPLEMENTED and registry.resolve_precomputed_field(
            node.name, node.params
        ) is None:
            problems.append(
                f"indicator {node.name!r} is registered but not yet implemented"
            )
        if not (0 <= node.offset <= MAX_OFFSET):
            problems.append(f"offset {node.offset} out of range for indicator {node.name!r}")
    elif isinstance(node, Literal):
        pass
    else:
        problems.append(f"unrecognized value node: {node!r}")
