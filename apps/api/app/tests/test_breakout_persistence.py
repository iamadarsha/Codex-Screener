"""Durable side effects — fake SQLAlchemy session (same pattern as
test_candles.py's `_FakeSession`, no real Postgres needed) + `fake_redis`
for the pubsub publish."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from app.breakouts import persistence
from app.breakouts.types import BreakoutSignal, BreakoutStatus, Direction, TriggerType


class _FakeResult:
    pass


class _FakeSession:
    instances: list["_FakeSession"] = []

    def __init__(self):
        self.added = []
        self.committed = False
        _FakeSession.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


@pytest.fixture(autouse=True)
def _reset_fake_sessions():
    _FakeSession.instances = []
    yield
    _FakeSession.instances = []


def _signal() -> BreakoutSignal:
    now = datetime(2026, 9, 15, 10, 5)
    return BreakoutSignal(
        symbol="RELIANCE",
        trigger_type=TriggerType.ORB,
        direction=Direction.BULLISH,
        status=BreakoutStatus.CONFIRMED,
        reference_level=Decimal("2500.0"),
        trigger_price=Decimal("2510.0"),
        confirmation_price=Decimal("2510.0"),
        triggered_at=now,
        confirmed_at=now,
        bars_confirmed=1,
        score=72.5,
    )


@pytest.mark.usefixtures("fake_redis")
async def test_publish_alert_trigger_matches_ws_alerts_expected_shape(fake_redis):
    pubsub = fake_redis.pubsub()
    await pubsub.subscribe("alert_triggers")

    alert_id = uuid.uuid4()
    await persistence.publish_alert_trigger(alert_id, _signal())

    # Drain the subscribe confirmation, then the actual message.
    await pubsub.get_message(timeout=1)
    message = await pubsub.get_message(timeout=1)
    payload = json.loads(message["data"])

    assert payload["alert_id"] == str(alert_id)
    assert payload["symbol"] == "RELIANCE"
    assert payload["trigger_price"] == 2510.0
    assert payload["conditions_met"] == [
        {"trigger_type": "orb", "direction": "bullish", "reference_level": 2500.0, "score": 72.5}
    ]


async def test_record_alert_history_writes_expected_row(monkeypatch):
    monkeypatch.setattr(persistence, "SessionLocal", _FakeSession)
    alert_id = uuid.uuid4()

    await persistence.record_alert_history(alert_id, _signal())

    assert len(_FakeSession.instances) == 1
    session = _FakeSession.instances[0]
    assert session.committed is True
    assert len(session.added) == 1
    row = session.added[0]
    assert row.alert_id == alert_id
    assert row.symbol == "RELIANCE"
    assert row.trigger_price == Decimal("2510.0")
    assert row.conditions_met[0]["trigger_type"] == "orb"


async def test_record_breakout_event_writes_expected_row(monkeypatch):
    monkeypatch.setattr(persistence, "SessionLocal", _FakeSession)

    await persistence.record_breakout_event(_signal())

    assert len(_FakeSession.instances) == 1
    session = _FakeSession.instances[0]
    assert session.committed is True
    row = session.added[0]
    assert row.symbol == "RELIANCE"
    assert row.trigger_type == "orb"
    assert row.direction == "bullish"
    assert row.reference_level == Decimal("2500.0")
    assert row.confirmation_price == Decimal("2510.0")
    assert row.score == 72.5


async def test_record_breakout_event_reuses_a_passed_in_session(monkeypatch):
    """A caller-provided session must be used directly — no new SessionLocal()
    checkout — so a signal's whole persistence path can share one connection.
    Caught live (2026-09-15): several symbols signalling in the same cycle
    each opened 2-3 separate connections, exhausting Supabase's small
    free-tier connection pool."""
    monkeypatch.setattr(persistence, "SessionLocal", _FakeSession)
    shared_session = _FakeSession()
    _FakeSession.instances.clear()  # the line above counts as one; reset for a clean assertion

    await persistence.record_breakout_event(_signal(), session=shared_session)

    assert _FakeSession.instances == []  # no new session opened
    assert shared_session.committed is True
    assert shared_session.added[0].symbol == "RELIANCE"


async def test_record_alert_history_reuses_a_passed_in_session(monkeypatch):
    monkeypatch.setattr(persistence, "SessionLocal", _FakeSession)
    shared_session = _FakeSession()
    _FakeSession.instances.clear()
    alert_id = uuid.uuid4()

    await persistence.record_alert_history(alert_id, _signal(), session=shared_session)

    assert _FakeSession.instances == []
    assert shared_session.committed is True
    assert shared_session.added[0].alert_id == alert_id
