"""Point-in-time scan/pattern replay engine.

Reuses BreakoutScan's own pure evaluation primitives unmodified:
`app.screener.dsl.evaluator.evaluate` / `EvalContext` for DSL scans,
`app.services.condition_evaluator.evaluate_conditions` for the legacy flat
shape, and `app.patterns.pattern_detector.detect_patterns` for pattern
scans — literally the same calls `screener_engine.run_scan()` makes today,
just fed as-of-safe historical inputs (a fresh, per-run
`SymbolIndicatorState` replayed bar-by-bar over `fetch_candle_history_as_of`
output) instead of a live Redis read.

This module must never call `now_ist()`, `market_open_today()`,
`get_market_state()` (the live singleton), or read any live Redis key
(`price:*`, `ind:*`). It is entirely self-contained from `as_of` +
Postgres history + fresh in-memory state, which is what makes point-in-time
correctness provable rather than merely asserted.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from app.market.candles import fetch_candle_history_as_of
from app.market.indicators import SymbolIndicatorState
from app.patterns.pattern_detector import detect_patterns
from app.research.evidence import validate_evidence
from app.screener.dsl.evaluator import EvalContext
from app.screener.dsl.evaluator import evaluate as dsl_evaluate
from app.services.condition_evaluator import Condition, evaluate_conditions

log = structlog.get_logger(__name__)


def build_scan_hash(scan_definition: dict[str, Any]) -> str:
    """Stable hash of a scan definition, used for manifest/evidence
    identity and (§ scan_version_check) determinism verification.

    `default=str` handles non-JSON-native members (a `dsl_root` `BoolNode`,
    or `Condition` dataclass instances in the legacy flat shape) by falling
    back to their `repr()` — deterministic for equal field values since
    these are all plain dataclasses, so two calls with equal-but-distinct
    scan definitions still hash identically.
    """
    payload = json.dumps(scan_definition, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _coerce_conditions(raw_conditions: list[Any]) -> list[Condition]:
    """Convert dict-shaped conditions (the JSON-over-the-wire form) into
    `Condition` objects — mirrors `screener_engine.run_custom_scan`'s
    dict-to-Condition conversion, duplicated in miniature here rather than
    importing it, so replay stays independent of the live engine module.
    `Condition` objects passed in directly (e.g. from a Python-level test)
    are passed through unchanged.
    """
    from app.services.condition_evaluator import (
        ConditionOperator,
        IndicatorRef,
        INDICATOR_NAMES,
        NumericLiteral,
    )

    op_map = {
        "gt": ConditionOperator.GREATER_THAN,
        "lt": ConditionOperator.LESS_THAN,
        "eq": ConditionOperator.EQUALS,
        "cross_above": ConditionOperator.CROSSES_ABOVE,
        "cross_below": ConditionOperator.CROSSES_BELOW,
    }

    parsed: list[Condition] = []
    for c in raw_conditions:
        if isinstance(c, Condition):
            parsed.append(c)
            continue
        if isinstance(c, dict):
            left = IndicatorRef(name=c.get("indicator", "close"))
            operator = op_map.get(c.get("operator", "gt"), ConditionOperator.GREATER_THAN)
            val = c.get("value", 0)
            right: Any
            if isinstance(val, str) and val in INDICATOR_NAMES:
                right = IndicatorRef(name=val)
            else:
                right = NumericLiteral(value=Decimal(str(val)))
            parsed.append(Condition(left=left, operator=operator, right=right))
    return parsed


async def replay_scan(
    run_id: str,
    scan_definition: dict[str, Any],
    universe_symbols: list[str],
    as_of: datetime,
    timeframe: str,
) -> dict[str, Any]:
    """Replay a scan/pattern definition against point-in-time historical
    data and return an evidence-gated result.

    For each symbol: fetch its candle history up to (and never past)
    `as_of` via `fetch_candle_history_as_of`, replay a *fresh*
    `SymbolIndicatorState` bar-by-bar over that history to reconstruct the
    indicator snapshot a live Redis `ind:{symbol}:{timeframe}` hash would
    have held at time `as_of`, then evaluate the scan's DSL tree / flat
    conditions and pattern name against that snapshot + candle list —
    using the exact same evaluation primitives the live screener uses.

    Evidence is validated *after* all data is loaded and *before* any
    signal is returned as trustworthy: on `"invalid"` evidence, the
    function returns `status: "FAILED"` with an empty `signals` list — an
    invalid-evidence run's would-be signals are never presented as if they
    were valid.
    """
    candles_by_symbol: dict[str, list[dict[str, Any]]] = {}
    snapshot_by_symbol: dict[str, dict[str, Any]] = {}

    for symbol in universe_symbols:
        candles = await fetch_candle_history_as_of(symbol, timeframe, as_of)
        candles_by_symbol[symbol] = candles

        state = SymbolIndicatorState()  # fresh per symbol, per replay run
        snapshot: dict[str, Any] = {}
        for candle in candles:
            snapshot = state.update(candle)
        snapshot_by_symbol[symbol] = snapshot

    scan_hash = build_scan_hash(scan_definition)
    evidence = validate_evidence(
        candles_by_symbol=candles_by_symbol,
        as_of=as_of,
        universe_symbols=universe_symbols,
        scan_hash=scan_hash,
    )

    if evidence.status == "invalid":
        log.warning(
            "replay_evidence_invalid",
            run_id=run_id,
            errors=evidence.errors,
        )
        return {
            "status": "FAILED",
            "evidence": evidence.model_dump(mode="json"),
            "signals": [],
        }

    dsl_root = scan_definition.get("dsl_root")
    raw_conditions = scan_definition.get("conditions") or []
    conditions = _coerce_conditions(raw_conditions) if raw_conditions else []
    pattern_name = scan_definition.get("pattern")

    has_filter = dsl_root is not None or bool(conditions) or bool(pattern_name)

    signals: list[dict[str, Any]] = []
    if has_filter:
        for symbol in universe_symbols:
            candles = candles_by_symbol.get(symbol, [])
            snapshot = snapshot_by_symbol.get(symbol, {})
            if not candles or not snapshot:
                continue

            condition_matched = True
            if dsl_root is not None:
                ctx = EvalContext(indicator_data=snapshot, candles=candles)
                condition_matched = dsl_evaluate(dsl_root, ctx)
            elif conditions:
                condition_matched = evaluate_conditions(conditions, snapshot, logic="AND")

            matched_patterns: list[dict[str, Any]] = []
            if pattern_name:
                detected = detect_patterns(candles)
                matched_patterns = [
                    {
                        "name": p.name,
                        "confidence": p.confidence,
                        "direction": p.direction.value,
                    }
                    for p in detected
                    if p.name == pattern_name
                ]

            pattern_matched = bool(matched_patterns) if pattern_name else True
            if not (condition_matched and pattern_matched):
                continue

            signals.append(
                {
                    "symbol": symbol,
                    "matched_conditions": condition_matched if (dsl_root or conditions) else None,
                    "matched_patterns": matched_patterns,
                    "indicator_snapshot": snapshot,
                }
            )

    log.info(
        "replay_complete",
        run_id=run_id,
        symbols_checked=len(universe_symbols),
        signals=len(signals),
    )

    return {
        "status": "SUCCEEDED",
        "evidence": evidence.model_dump(mode="json"),
        "summary": {"signals": len(signals), "symbols_checked": len(universe_symbols)},
        "signals": signals,
    }
