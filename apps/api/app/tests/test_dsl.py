"""Scan DSL: parser, validator, compiler, evaluator, serializer
(Phase 3.1 acceptance gates)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.screener.dsl.ast import BoolAnd, BoolOr, Comparison, CompareOp, IndicatorCall, PriceField
from app.screener.dsl.compiler import compile_batch, compile_scan
from app.screener.dsl.evaluator import EvalContext, evaluate
from app.screener.dsl.parser import DslParseError, parse_scan
from app.screener.dsl.serializer import bool_to_json
from app.screener.dsl.validator import DslValidationError, validate


def _synthetic_candles(n: int, start: float = 100.0, step: float = 1.0) -> list[dict]:
    """A strictly increasing close-price series — easy to reason about for
    offset/rolling/crossover tests."""
    candles = []
    price = start
    for i in range(n):
        candles.append(
            {
                "open": price - 0.5,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": 1000 + i,
            }
        )
        price += step
    return candles


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_simple_comparison():
    root = parse_scan({"left": {"field": "close"}, "op": "gt", "right": 100})
    assert isinstance(root, Comparison)
    assert isinstance(root.left, PriceField)
    assert root.op is CompareOp.GT


def test_parses_nested_and_or_not():
    root = parse_scan(
        {
            "and": [
                {"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 50},
                {
                    "or": [
                        {"crosses_above": {"left": {"field": "close"}, "right": {"indicator": "ema", "length": 20}}},
                        {"not": {"left": {"field": "volume"}, "op": "lt", "right": 1000}},
                    ]
                },
            ]
        }
    )
    assert isinstance(root, BoolAnd)
    assert len(root.clauses) == 2
    assert isinstance(root.clauses[1], BoolOr)


def test_indicator_params_are_canonicalized_with_defaults():
    root = parse_scan({"left": {"indicator": "macd", "fast": 12}, "op": "gt", "right": 0})
    left = root.left
    assert isinstance(left, IndicatorCall)
    # slow/signal defaults filled in even though only "fast" was specified
    assert dict(left.params) == {"fast": 12, "slow": 26, "signal": 9}


def test_malformed_input_raises_parse_error():
    with pytest.raises(DslParseError):
        parse_scan({"and": []})  # empty group
    with pytest.raises(DslParseError):
        parse_scan({"left": {"field": "close"}, "op": "wat", "right": 1})
    with pytest.raises(DslParseError):
        parse_scan({"field": "not_a_real_field"})


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def test_validator_accepts_well_formed_tree():
    root = parse_scan({"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 50})
    validate(root)  # should not raise


def test_validator_rejects_unknown_indicator():
    root = Comparison(
        left=IndicatorCall(name="not_a_real_indicator"), op=CompareOp.GT, right=None
    )
    with pytest.raises(DslValidationError):
        validate(root)


def test_validator_rejects_not_yet_implemented_indicator():
    root = Comparison(left=IndicatorCall(name="cci"), op=CompareOp.GT, right=None)
    with pytest.raises(DslValidationError) as exc_info:
        validate(root)
    assert any("not yet implemented" in p for p in exc_info.value.problems)


def test_validator_rejects_absurd_offset():
    root = Comparison(left=PriceField(name="close", offset=999999), op=CompareOp.GT, right=None)
    with pytest.raises(DslValidationError):
        validate(root)


def test_validator_rejects_invalid_timeframe():
    root = parse_scan({"left": {"field": "close"}, "op": "gt", "right": 1})
    with pytest.raises(DslValidationError):
        validate(root, timeframe="17_fortnights")


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------


def test_compiler_dedupes_shared_indicator_across_scans():
    scan_a = parse_scan({"left": {"indicator": "ema", "length": 9}, "op": "gt", "right": 100})
    scan_b = parse_scan({"left": {"indicator": "ema", "length": 9}, "op": "lt", "right": 200})
    scan_c = parse_scan({"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 30})

    batch = compile_batch([scan_a, scan_b, scan_c])

    # 3 scans reference 2 distinct indicators total (ema_9 shared, rsi_14 once) —
    # verified by actually counting the deduped requirement set, not asserted.
    reqs = batch.unique_requirements
    indicator_names = {r.name for r in reqs if r.kind == "indicator"}
    assert indicator_names == {"ema", "rsi"}
    assert len(reqs) == 2


def test_compiler_merges_max_offset_across_scans():
    scan_a = parse_scan({"left": {"field": "close", "offset": 2}, "op": "gt", "right": 1})
    scan_b = parse_scan({"left": {"field": "close", "offset": 9}, "op": "gt", "right": 1})

    batch = compile_batch([scan_a, scan_b])
    close_reqs = [r for r in batch.unique_requirements if r.name == "close"]
    assert len(close_reqs) == 1
    assert close_reqs[0].max_offset == 9  # the larger of the two, not both kept separately


def test_crossover_requirement_implies_at_least_one_bar_of_history():
    scan = parse_scan(
        {"crosses_above": {"left": {"field": "close"}, "right": {"indicator": "ema", "length": 9}}}
    )
    compiled = compile_scan(scan)
    close_req = next(r for r in compiled.requirements if r.name == "close")
    assert close_req.max_offset >= 1


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


def test_evaluates_simple_comparison_true_and_false():
    candles = _synthetic_candles(5, start=100.0)
    ctx = EvalContext(indicator_data={}, candles=candles)

    assert evaluate(parse_scan({"left": {"field": "close"}, "op": "gt", "right": 50}), ctx) is True
    assert evaluate(parse_scan({"left": {"field": "close"}, "op": "gt", "right": 500}), ctx) is False


def test_historical_offset_reads_actual_history_not_just_bar_minus_one():
    # Prices climb 100, 101, ..., 109 (index i -> price 100+i). offset=5 from
    # the last bar (index 9, price 109) should be index 4 (price 104).
    candles = _synthetic_candles(10, start=100.0)
    ctx = EvalContext(indicator_data={}, candles=candles)

    root = parse_scan({"left": {"field": "close", "offset": 5}, "op": "eq", "right": 104})
    assert evaluate(root, ctx) is True


def test_rolling_highest_and_lowest():
    candles = _synthetic_candles(20, start=100.0)  # high = close+1, so highs go 101..120
    ctx = EvalContext(indicator_data={}, candles=candles)

    root = parse_scan(
        {"left": {"rolling": "highest", "of": {"field": "high"}, "n": 5}, "op": "eq", "right": 120}
    )
    assert evaluate(root, ctx) is True  # last 5 highs: 116..120, highest=120


def test_rolling_count_predicate():
    # 10 candles, close > 104 is true for the last 5 (105..109... wait indices)
    candles = _synthetic_candles(10, start=100.0)  # closes: 100..109
    ctx = EvalContext(indicator_data={}, candles=candles)

    root = parse_scan(
        {
            "left": {
                "rolling": "count",
                "n": 10,
                "predicate": {"left": {"field": "close"}, "op": "gt", "right": 104},
            },
            "op": "gte",
            "right": 5,
        }
    )
    # closes 105..109 (5 values) are > 104 out of the last 10 bars
    assert evaluate(root, ctx) is True


def test_crosses_above_detects_real_crossover_not_bare_inequality():
    root = parse_scan({"crosses_above": {"left": {"field": "close"}, "right": {"literal": 100}}})

    candles2 = [
        {"open": 0, "high": 0, "low": 0, "close": 99, "volume": 0},
        {"open": 0, "high": 0, "low": 0, "close": 100, "volume": 0},
        {"open": 0, "high": 0, "low": 0, "close": 101, "volume": 0},
    ]
    ctx2 = EvalContext(indicator_data={}, candles=candles2)
    # prev (100) <= 100 and now (101) > 100 -> True crossover
    assert evaluate(root, ctx2) is True

    candles3 = [
        {"open": 0, "high": 0, "low": 0, "close": 101, "volume": 0},
        {"open": 0, "high": 0, "low": 0, "close": 102, "volume": 0},
    ]
    ctx3 = EvalContext(indicator_data={}, candles=candles3)
    # prev (101) already > 100 -- currently greater, but NOT a crossover
    assert evaluate(root, ctx3) is False


def test_fast_path_uses_precomputed_indicator_hash_when_offset_zero():
    # No candle history at all — only the precomputed hash — should still work.
    ctx = EvalContext(indicator_data={"rsi_14": "72.5"}, candles=[])
    root = parse_scan({"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 70})
    assert evaluate(root, ctx) is True


def test_on_the_fly_indicator_matches_incremental_state_directly():
    from app.market.indicators import SmaState

    candles = _synthetic_candles(25, start=50.0)
    ctx = EvalContext(indicator_data={}, candles=candles)

    # SMA(25) with no precomputed hash field for that length -> forces the
    # on-the-fly path. Cross-check against feeding SmaState directly.
    state = SmaState(25)
    expected = None
    for c in candles:
        expected = state.update(c["close"])

    root = parse_scan({"left": {"indicator": "sma", "length": 25}, "op": "eq", "right": float(expected)})
    assert evaluate(root, ctx) is True


def test_missing_data_evaluates_false_not_an_exception():
    ctx = EvalContext(indicator_data={}, candles=[])
    root = parse_scan({"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 50})
    assert evaluate(root, ctx) is False


# ---------------------------------------------------------------------------
# Serializer round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wire",
    [
        {"left": {"field": "close"}, "op": "gt", "right": 100},
        {
            "and": [
                {"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 50},
                {"not": {"left": {"field": "volume"}, "op": "lt", "right": 1000}},
            ]
        },
        {"crosses_above": {"left": {"field": "close"}, "right": {"indicator": "ema", "length": 9}}},
        {"left": {"rolling": "avg", "of": {"field": "close"}, "n": 20}, "op": "gt", "right": 100},
    ],
)
def test_serializer_round_trips_through_parser(wire):
    root = parse_scan(wire)
    reparsed = parse_scan(bool_to_json(root))
    assert reparsed == root
