"""Compile a validated DSL tree into a requirement set (master prompt §29's
dependency graph, in its practical form).

Each scan compiles to the exact set of data points it needs. When multiple
scans compile together in one `CompiledBatch` (the normal case — a screener
run evaluates many scans against the same universe), requirements are
deduped by `(kind, name, params)` with the *maximum* requested historical
offset merged in, so a shared indicator like `EMA(9)` referenced by five
different scans is resolved once per symbol with enough history for all
five, not five separate times.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
    RollingFunction,
)


@dataclass(frozen=True, slots=True)
class Requirement:
    """One concrete piece of data a compiled scan needs.

    `max_offset` is how many bars of history are needed for this data point
    (0 = only the current value). Two requirements with the same
    `(kind, name, params)` but different offsets should be merged, not kept
    separate — see `_merge_requirement`.
    """

    kind: str  # "price_field" | "indicator"
    name: str
    params: tuple[tuple[str, int], ...] = ()
    max_offset: int = 0

    @property
    def key(self) -> tuple[str, str, tuple[tuple[str, int], ...]]:
        return (self.kind, self.name, self.params)

    @property
    def needs_history(self) -> bool:
        return self.max_offset > 0


@dataclass(frozen=True, slots=True)
class CompiledScan:
    root: BoolNode
    requirements: frozenset[Requirement]


@dataclass
class CompiledBatch:
    scans: list[CompiledScan] = field(default_factory=list)

    @property
    def unique_requirements(self) -> frozenset[Requirement]:
        merged: dict[tuple, Requirement] = {}
        for scan in self.scans:
            for req in scan.requirements:
                _merge_requirement(merged, req)
        return frozenset(merged.values())


def _merge_requirement(acc: dict[tuple, "Requirement"], req: "Requirement") -> None:
    existing = acc.get(req.key)
    if existing is None or req.max_offset > existing.max_offset:
        acc[req.key] = req


def compile_scan(root: BoolNode) -> CompiledScan:
    acc: dict[tuple, Requirement] = {}
    _collect_bool(root, acc)
    return CompiledScan(root=root, requirements=frozenset(acc.values()))


def compile_batch(roots: list[BoolNode]) -> CompiledBatch:
    return CompiledBatch(scans=[compile_scan(r) for r in roots])


def _collect_bool(node: BoolNode, acc: dict[tuple, Requirement]) -> None:
    if isinstance(node, (BoolAnd, BoolOr)):
        for c in node.clauses:
            _collect_bool(c, acc)
    elif isinstance(node, BoolNot):
        _collect_bool(node.clause, acc)
    elif isinstance(node, Comparison):
        _collect_aggregatable(node.left, acc)
        _collect_aggregatable(node.right, acc)
    elif isinstance(node, (CrossesAbove, CrossesBelow)):
        # A crossover always needs the previous bar too.
        _collect_value(node.left, acc, min_offset=1)
        _collect_value(node.right, acc, min_offset=1)


def _collect_aggregatable(node, acc: dict[tuple, Requirement]) -> None:
    if isinstance(node, RollingFunction):
        if node.predicate is not None:
            _collect_aggregatable(node.predicate.left, acc)
            _collect_aggregatable(node.predicate.right, acc)
        if node.expr is not None:
            _collect_value(node.expr, acc, min_offset=node.n - 1)
    else:
        _collect_value(node, acc)


def _collect_value(node, acc: dict[tuple, Requirement], min_offset: int = 0) -> None:
    if isinstance(node, PriceField):
        offset = max(node.offset, min_offset)
        req = Requirement(kind="price_field", name=node.name, max_offset=offset)
        _merge_requirement(acc, req)
    elif isinstance(node, IndicatorCall):
        offset = max(node.offset, min_offset)
        req = Requirement(kind="indicator", name=node.name, params=node.params, max_offset=offset)
        _merge_requirement(acc, req)
    elif isinstance(node, Literal):
        pass
