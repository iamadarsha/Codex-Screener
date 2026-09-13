"""AST -> JSON serialization (the inverse of parser.py).

Needed for saved-scan storage, shareable scan URLs, and JSON DSL
export/import (master prompt §59/§61) — deferred features, but the
round-trip itself is cheap to build now and is exercised by tests to keep
parser.py and serializer.py honest against each other.
"""

from __future__ import annotations

from typing import Any

from app.screener.dsl.ast import (
    AggregatableNode,
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
    RollingFunction,
    ValueNode,
)


def value_to_json(node: ValueNode) -> Any:
    if isinstance(node, Literal):
        return node.value
    if isinstance(node, PriceField):
        out: dict[str, Any] = {"field": node.name}
        if node.offset:
            out["offset"] = node.offset
        return out
    if isinstance(node, IndicatorCall):
        out = {"indicator": node.name}
        out.update(dict(node.params))
        if node.offset:
            out["offset"] = node.offset
        return out
    raise TypeError(f"unhandled value node: {node!r}")


def aggregatable_to_json(node: AggregatableNode) -> Any:
    if isinstance(node, RollingFunction):
        out: dict[str, Any] = {"rolling": node.fn.value, "n": node.n}
        if node.predicate is not None:
            out["predicate"] = comparison_to_json(node.predicate)
        if node.expr is not None:
            out["of"] = value_to_json(node.expr)
        return out
    return value_to_json(node)


def comparison_to_json(node: Comparison) -> dict[str, Any]:
    return {
        "left": aggregatable_to_json(node.left),
        "op": node.op.value,
        "right": aggregatable_to_json(node.right),
    }


def bool_to_json(node: BoolNode) -> dict[str, Any]:
    if isinstance(node, BoolAnd):
        return {"and": [bool_to_json(c) for c in node.clauses]}
    if isinstance(node, BoolOr):
        return {"or": [bool_to_json(c) for c in node.clauses]}
    if isinstance(node, BoolNot):
        return {"not": bool_to_json(node.clause)}
    if isinstance(node, CrossesAbove):
        return {
            "crosses_above": {
                "left": value_to_json(node.left),
                "right": value_to_json(node.right),
            }
        }
    if isinstance(node, CrossesBelow):
        return {
            "crosses_below": {
                "left": value_to_json(node.left),
                "right": value_to_json(node.right),
            }
        }
    if isinstance(node, Comparison):
        return comparison_to_json(node)
    raise TypeError(f"unhandled bool node: {node!r}")
