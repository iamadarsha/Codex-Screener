"""Parse JSON scan definitions into the DSL AST (ast.py).

Wire grammar (all dict-based, recursive):

Value expressions:
    {"field": "close"}                          -> PriceField
    {"field": "close", "offset": 5}              -> PriceField, 5 bars back
    {"indicator": "rsi", "length": 14}           -> IndicatorCall (extra
                                                     keys besides "indicator"/
                                                     "offset" become params)
    {"indicator": "sma", "length": 20, "offset": 3}
    30 | 30.5                                    -> Literal (bare number)
    {"literal": 30}                              -> Literal (explicit form)

Rolling functions:
    {"rolling": "highest", "of": {"field": "high"}, "n": 20}
    {"rolling": "count", "predicate": {...comparison...}, "n": 10}

Comparisons / crossovers (bool leaves):
    {"left": <value>, "op": "gt", "right": <value>}
    {"crosses_above": {"left": <value>, "right": <value>}}
    {"crosses_below": {"left": <value>, "right": <value>}}

Boolean groups:
    {"and": [<bool-node>, ...]}
    {"or": [<bool-node>, ...]}
    {"not": <bool-node>}

This is entirely additive — the existing flat `ScanCondition` shape used by
`POST /api/screener/custom` today is untouched and keeps going through
`app.services.condition_evaluator` unchanged. This parser is the entry
point for the new `dsl` field only (see the Phase 3.1 plan).
"""

from __future__ import annotations

from typing import Any

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

_PRICE_FIELDS = frozenset({"open", "high", "low", "close", "volume"})

_COMPARE_OPS = {
    "gt": CompareOp.GT,
    ">": CompareOp.GT,
    "lt": CompareOp.LT,
    "<": CompareOp.LT,
    "gte": CompareOp.GTE,
    ">=": CompareOp.GTE,
    "lte": CompareOp.LTE,
    "<=": CompareOp.LTE,
    "eq": CompareOp.EQ,
    "==": CompareOp.EQ,
    "neq": CompareOp.NEQ,
    "!=": CompareOp.NEQ,
}

_ROLLING_FNS = {fn.value: fn for fn in RollingFn}


class DslParseError(ValueError):
    """Raised when a scan definition doesn't match the DSL grammar."""


def parse_value(node: Any) -> ValueNode:
    """Parse a value-expression node (not a rolling function)."""
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        return Literal(float(node))

    if not isinstance(node, dict):
        raise DslParseError(f"expected a value expression dict or number, got {node!r}")

    if "literal" in node:
        return Literal(float(node["literal"]))

    if "field" in node:
        name = node["field"]
        if name not in _PRICE_FIELDS:
            raise DslParseError(f"unknown price field {name!r}")
        offset = int(node.get("offset", 0))
        return PriceField(name=name, offset=offset)

    if "indicator" in node:
        name = node["indicator"]
        offset = int(node.get("offset", 0))
        raw_params = {k: int(v) for k, v in node.items() if k not in ("indicator", "offset")}
        canonical = registry.canonical_params(
            tuple(sorted(raw_params.items())), registry.default_params(name)
        )
        return IndicatorCall(name=name, params=canonical, offset=offset)

    raise DslParseError(f"could not parse value expression: {node!r}")


def parse_aggregatable(node: Any) -> AggregatableNode:
    """A value expression OR a rolling function — used on either side of a
    comparison and as a rolling function's `of` operand."""
    if isinstance(node, dict) and "rolling" in node:
        return parse_rolling_function(node)
    return parse_value(node)


def parse_rolling_function(node: dict) -> RollingFunction:
    fn_name = node.get("rolling")
    fn = _ROLLING_FNS.get(fn_name)
    if fn is None:
        raise DslParseError(f"unknown rolling function {fn_name!r}")

    n = node.get("n")
    if not isinstance(n, int) or n <= 0:
        raise DslParseError(f"rolling function {fn_name!r} needs a positive integer 'n'")

    if fn is RollingFn.COUNT:
        predicate_node = node.get("predicate")
        if predicate_node is None:
            raise DslParseError("COUNT rolling function requires a 'predicate'")
        return RollingFunction(fn=fn, n=n, predicate=parse_comparison(predicate_node))

    of_node = node.get("of")
    if of_node is None:
        raise DslParseError(f"rolling function {fn_name!r} requires an 'of' expression")
    return RollingFunction(fn=fn, n=n, expr=parse_value(of_node))


def parse_comparison(node: dict) -> Comparison:
    if "left" not in node or "op" not in node or "right" not in node:
        raise DslParseError(f"comparison requires left/op/right: {node!r}")
    op = _COMPARE_OPS.get(node["op"])
    if op is None:
        raise DslParseError(f"unknown comparison operator {node['op']!r}")
    return Comparison(
        left=parse_aggregatable(node["left"]),
        op=op,
        right=parse_aggregatable(node["right"]),
    )


def parse_bool_node(node: Any) -> BoolNode:
    if not isinstance(node, dict):
        raise DslParseError(f"expected a bool-node dict, got {node!r}")

    if "and" in node:
        clauses = node["and"]
        if not isinstance(clauses, list) or not clauses:
            raise DslParseError("'and' requires a non-empty list")
        return BoolAnd(tuple(parse_bool_node(c) for c in clauses))

    if "or" in node:
        clauses = node["or"]
        if not isinstance(clauses, list) or not clauses:
            raise DslParseError("'or' requires a non-empty list")
        return BoolOr(tuple(parse_bool_node(c) for c in clauses))

    if "not" in node:
        return BoolNot(parse_bool_node(node["not"]))

    if "crosses_above" in node:
        inner = node["crosses_above"]
        return CrossesAbove(left=parse_value(inner["left"]), right=parse_value(inner["right"]))

    if "crosses_below" in node:
        inner = node["crosses_below"]
        return CrossesBelow(left=parse_value(inner["left"]), right=parse_value(inner["right"]))

    if "left" in node and "op" in node and "right" in node:
        return parse_comparison(node)

    raise DslParseError(f"could not parse bool node: {node!r}")


def parse_scan(definition: dict) -> BoolNode:
    """Top-level entry point: parse a full scan definition's root node."""
    return parse_bool_node(definition)
