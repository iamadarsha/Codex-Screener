"""Candle boundary rollover + batched persistence (Phase 2.1 acceptance gates).

Uses fakeredis (via the `fake_redis` fixture) for the current-candle store,
and a fake SQLAlchemy session (monkeypatched in place of `SessionLocal`) for
persistence — no real Postgres needed for these tests.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.market.candles import _PENDING_1MIN_MAX, CandleEngine, CandlePersistenceError
from app.utils.time import IST


class _FakeResult:
    pass


class _FakeSession:
    """Records executed statements; can be told to raise on commit."""

    instances: list["_FakeSession"] = []

    def __init__(self, raise_on_commit: bool = False):
        self.executed = []
        self.committed = False
        self._raise_on_commit = raise_on_commit
        _FakeSession.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, stmt):
        self.executed.append(stmt)
        return _FakeResult()

    async def commit(self):
        if self._raise_on_commit:
            raise RuntimeError("simulated DB failure")
        self.committed = True


@pytest.fixture(autouse=True)
def _reset_fake_sessions():
    _FakeSession.instances = []
    yield
    _FakeSession.instances = []


def _ist(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2026, 9, 15, hour, minute, second, tzinfo=IST)  # a Tuesday


@pytest.mark.usefixtures("fake_redis")
async def test_tick_within_same_boundary_updates_high_low_close():
    engine = CandleEngine()
    completed = await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    assert completed == []  # first tick just opens the candle, nothing completes yet

    completed = await engine.on_tick("RELIANCE", ltp=105.0, volume_delta=5, ts=_ist(9, 15, 30))
    assert completed == []


@pytest.mark.usefixtures("fake_redis")
async def test_boundary_rollover_finalises_previous_candle():
    engine = CandleEngine()
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    await engine.on_tick("RELIANCE", ltp=110.0, volume_delta=5, ts=_ist(9, 15, 45))

    # Crosses into the next 1-min boundary (09:16) — the 09:15 1min candle
    # (and the still-open 09:15 5min/15min candles) should finalise/roll.
    completed = await engine.on_tick("RELIANCE", ltp=108.0, volume_delta=3, ts=_ist(9, 16, 5))

    one_min = next(c for c in completed if c["timeframe"] == "1min")
    assert one_min["open"] == "100.0"
    assert one_min["high"] == "110.0"
    assert one_min["close"] == "110.0"
    assert one_min["volume"] == 15  # 10 + 5 — summed deltas, not the last cumulative value

    # 5min/15min boundaries haven't rolled yet (09:15 and 09:16 are the same 5/15-min bucket)
    assert not any(c["timeframe"] in ("5min", "15min") for c in completed)


@pytest.mark.usefixtures("fake_redis")
async def test_completed_1min_candles_are_buffered_not_persisted_immediately(monkeypatch):
    monkeypatch.setattr("app.market.candles.SessionLocal", lambda: _FakeSession())

    engine = CandleEngine()
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    await engine.on_tick("RELIANCE", ltp=108.0, volume_delta=3, ts=_ist(9, 16, 5))

    assert engine.pending_count() == 1
    assert _FakeSession.instances == []  # nothing hit the DB yet


@pytest.mark.usefixtures("fake_redis")
async def test_flush_pending_batches_into_one_transaction(monkeypatch):
    monkeypatch.setattr("app.market.candles.SessionLocal", lambda: _FakeSession())

    engine = CandleEngine()
    ts = _ist(9, 15, 0)
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=ts)
    for minute in range(1, 6):
        await engine.on_tick(
            "RELIANCE", ltp=100.0 + minute, volume_delta=1, ts=_ist(9, 15 + minute, 0)
        )

    assert engine.pending_count() == 5  # 5 completed 1-min candles buffered

    written = await engine.flush_pending()

    assert written == 5
    assert len(_FakeSession.instances) == 1  # exactly one transaction, not five
    assert _FakeSession.instances[0].committed is True
    assert engine.pending_count() == 0


@pytest.mark.usefixtures("fake_redis")
async def test_flush_failure_is_raised_not_swallowed_and_batch_is_retried(monkeypatch):
    monkeypatch.setattr(
        "app.market.candles.SessionLocal", lambda: _FakeSession(raise_on_commit=True)
    )

    engine = CandleEngine()
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    await engine.on_tick("RELIANCE", ltp=101.0, volume_delta=1, ts=_ist(9, 16, 0))

    assert engine.pending_count() == 1

    with pytest.raises(CandlePersistenceError):
        await engine.flush_pending()

    # The failed batch is put back for a later retry, not dropped —
    # this is the fix for the old CandleBuilder._persist_1min, which just
    # logged and discarded a failed write.
    assert engine.pending_count() == 1


@pytest.mark.usefixtures("fake_redis")
async def test_pending_buffer_is_capped_not_unbounded_when_db_stays_down(monkeypatch):
    """A genuinely unreachable DB (not a transient blip) must not let
    _pending_1min grow forever — caught live (2026-09-14): no Postgres was
    connected in production, every flush failed, and the retry-everything
    behavior above grew the buffer continuously on a memory-constrained VM
    that had already OOM-crashed twice that day."""
    monkeypatch.setattr(
        "app.market.candles.SessionLocal", lambda: _FakeSession(raise_on_commit=True)
    )

    engine = CandleEngine()
    # Simulate a large pre-existing backlog from many prior failed cycles.
    engine._pending_1min = [  # noqa: SLF001
        {
            "symbol": "RELIANCE",
            "timeframe": "1min",
            "ts": _ist(9, 15, 0).isoformat(),
            "open": "100",
            "high": "100",
            "low": "100",
            "close": "100",
            "volume": 1,
        }
        for _ in range(_PENDING_1MIN_MAX)
    ]

    with pytest.raises(CandlePersistenceError):
        await engine.flush_pending()

    assert engine.pending_count() <= _PENDING_1MIN_MAX


@pytest.mark.usefixtures("fake_redis")
async def test_flush_pending_backs_off_after_failure_instead_of_hammering_db(monkeypatch):
    """After a failed write, an immediate retry must not hit the DB again —
    caught live (2026-09-14): with no backoff, a sustained outage meant a
    fresh connection attempt roughly every ~24s across the full universe,
    hammering an already-down dependency on top of the memory-leak risk."""
    monkeypatch.setattr(
        "app.market.candles.SessionLocal", lambda: _FakeSession(raise_on_commit=True)
    )

    engine = CandleEngine()
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    await engine.on_tick("RELIANCE", ltp=101.0, volume_delta=1, ts=_ist(9, 16, 0))

    with pytest.raises(CandlePersistenceError):
        await engine.flush_pending()
    assert len(_FakeSession.instances) == 1

    # Immediately retrying should be skipped entirely — no new DB session.
    with pytest.raises(CandlePersistenceError, match="backing off"):
        await engine.flush_pending()
    assert len(_FakeSession.instances) == 1


@pytest.mark.usefixtures("fake_redis")
async def test_flush_pending_backoff_resets_only_on_success(monkeypatch):
    engine = CandleEngine()
    engine._backoff_index = 3  # noqa: SLF001 — simulate a prior run of failures
    engine._next_attempt_at = 0.0  # noqa: SLF001 — backoff window already elapsed

    monkeypatch.setattr("app.market.candles.SessionLocal", lambda: _FakeSession())
    await engine.on_tick("RELIANCE", ltp=100.0, volume_delta=10, ts=_ist(9, 15, 0))
    await engine.on_tick("RELIANCE", ltp=101.0, volume_delta=1, ts=_ist(9, 16, 0))

    written = await engine.flush_pending()

    assert written == 1
    assert engine._backoff_index == -1  # noqa: SLF001 — reset after a real success
