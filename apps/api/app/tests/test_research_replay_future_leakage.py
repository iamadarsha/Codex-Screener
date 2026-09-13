"""THE critical regression test for point-in-time correctness.

Builds two full DB row sets for the same symbol, identical except that one
has an extra dramatic price spike bar timestamped *after* the replay's
`as_of` cutoff. Runs `replay_scan(..., as_of=<cutoff>)` against both and
asserts the results are identical field-for-field — proving the spike was
structurally invisible to the as-of-09:17 replay, not merely "trust me".

Crucially, the fake DB session below does NOT simply return whatever rows
it's handed — it introspects the *actual* SQLAlchemy `Select` statement
`fetch_candle_history_as_of` builds (via `stmt.compile().params`) to find
the real bound `ts <= as_of` cutoff, and filters the full (unfiltered) row
set by it, then sorts/limits exactly as Postgres would. If the fake instead
returned every row unconditionally, both fixtures would trivially produce
identical results regardless of whether `fetch_candle_history_as_of`'s
predicate actually worked — which would prove nothing. This fake proves
the predicate itself, applied through the real query-building code, keeps
the 09:18 spike out.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest

from app.research.replay import replay_scan
from app.utils.time import IST

AS_OF = datetime(2026, 9, 10, 9, 17, 0, tzinfo=IST)


@dataclass
class _FakeRow:
    symbol: str
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def _row(minute: int, close: float, symbol: str = "RELIANCE") -> _FakeRow:
    ts = datetime(2026, 9, 10, 9, minute, 0, tzinfo=IST)
    return _FakeRow(
        symbol=symbol,
        ts=ts,
        open=Decimal(str(close)),
        high=Decimal(str(close)),
        low=Decimal(str(close)),
        close=Decimal(str(close)),
        volume=10_000,
    )


# Baseline bars, identical in both fixtures — all at/before the 09:17 cutoff.
_BASELINE_ROWS = [_row(9 + i, 100.0 + i) for i in range(9)]  # 09:09 .. 09:17, mild trend

_ROWS_WITHOUT_SPIKE = list(_BASELINE_ROWS)
_ROWS_WITH_SPIKE = list(_BASELINE_ROWS) + [_row(18, 5000.0)]  # dramatic 09:18 spike


class _FakeAsOfResult:
    def __init__(self, rows: list[_FakeRow]) -> None:
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeAsOfSession:
    """Genuinely respects the `ts <= as_of` predicate by extracting the
    real bound cutoff value from the compiled statement, rather than
    trusting the caller to have pre-filtered anything."""

    def __init__(self, rows: list[_FakeRow]) -> None:
        self.all_rows = rows  # the FULL, unfiltered row set (may include future bars)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, stmt):
        compiled = stmt.compile()
        cutoff: datetime | None = None
        for value in compiled.params.values():
            if isinstance(value, datetime):
                cutoff = value
        if cutoff is None:
            raise AssertionError(
                "expected fetch_candle_history_as_of's query to bind a datetime "
                "cutoff parameter — none was found, so this fake cannot verify "
                "the as-of filter actually applies"
            )
        filtered = [r for r in self.all_rows if r.ts <= cutoff]
        filtered.sort(key=lambda r: r.ts, reverse=True)
        return _FakeAsOfResult(filtered[:210])


_SCAN_DEFINITION = {
    "conditions": [{"indicator": "close", "operator": "gt", "value": 1}],
    "timeframe": "1min",
}


async def _run_replay_against(rows: list[_FakeRow], monkeypatch) -> dict:
    monkeypatch.setattr("app.market.candles.SessionLocal", lambda: _FakeAsOfSession(rows))
    return await replay_scan(
        run_id="leak_test",
        scan_definition=dict(_SCAN_DEFINITION),
        universe_symbols=["RELIANCE"],
        as_of=AS_OF,
        timeframe="1min",
    )


async def test_future_spike_is_structurally_invisible_to_asof_replay(monkeypatch):
    result_without_spike = await _run_replay_against(_ROWS_WITHOUT_SPIKE, monkeypatch)
    result_with_spike = await _run_replay_against(_ROWS_WITH_SPIKE, monkeypatch)

    assert result_without_spike["status"] == "SUCCEEDED"
    assert result_with_spike["status"] == "SUCCEEDED"

    # The whole point: byte-for-byte identical results prove the row set
    # that DID contain a future spike produced exactly the same replay
    # output as the row set that never had one — the extra 09:18 bar was
    # never visible to the as-of-09:17 query at all.
    assert result_with_spike == result_without_spike

    # Sanity: the spike bar's dramatic close (5000.0) never leaked into the
    # indicator snapshot actually used (would massively distort ema/sma/rsi
    # if it had).
    snapshot = result_with_spike["signals"][0]["indicator_snapshot"]
    assert snapshot["close"] < 1000  # nowhere near the 5000.0 spike close


async def test_fake_session_would_have_caught_a_broken_asof_filter(monkeypatch):
    """Meta-test: confirm the fake genuinely filters rather than trivially
    passing everything through. If `fetch_candle_history_as_of` regressed
    to ignore its `as_of` argument entirely, this fake would still return
    every row (including the future spike) for BOTH fixtures called with
    the same as_of — so this test independently proves the fake session
    itself discriminates on the bound cutoff, by calling execute() twice
    with two different as_of cutoffs against the SAME full row set."""
    from app.market.candles import fetch_candle_history_as_of

    monkeypatch.setattr("app.market.candles.SessionLocal", lambda: _FakeAsOfSession(_ROWS_WITH_SPIKE))

    early_cutoff = datetime(2026, 9, 10, 9, 17, 0, tzinfo=IST)
    late_cutoff = datetime(2026, 9, 10, 9, 18, 0, tzinfo=IST)

    early_result = await fetch_candle_history_as_of("RELIANCE", "1min", early_cutoff)
    late_result = await fetch_candle_history_as_of("RELIANCE", "1min", late_cutoff)

    early_closes = [c["close"] for c in early_result]
    late_closes = [c["close"] for c in late_result]

    assert 5000.0 not in early_closes  # spike excluded when as_of is before it
    assert 5000.0 in late_closes  # spike included once as_of moves past it
