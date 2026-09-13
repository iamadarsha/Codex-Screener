"""Alert-notification dedupe against fake Redis."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest

from app.breakouts.dedupe import should_notify
from app.breakouts.types import BreakoutSignal, BreakoutStatus, Direction, TriggerType


@dataclass
class _FakeAlert:
    id: uuid.UUID
    frequency: str


def _signal(symbol: str = "RELIANCE") -> BreakoutSignal:
    now = datetime(2026, 9, 15, 10, 0)
    return BreakoutSignal(
        symbol=symbol,
        trigger_type=TriggerType.ORB,
        direction=Direction.BULLISH,
        status=BreakoutStatus.CONFIRMED,
        reference_level=Decimal(100),
        trigger_price=Decimal(101),
        confirmation_price=Decimal(101),
        triggered_at=now,
        confirmed_at=now,
        bars_confirmed=1,
    )


@pytest.mark.usefixtures("fake_redis")
async def test_every_time_always_notifies():
    alert = _FakeAlert(id=uuid.uuid4(), frequency="every_time")
    now = datetime(2026, 9, 15, 10, 0)
    assert await should_notify(alert, _signal(), now) is True
    assert await should_notify(alert, _signal(), now) is True  # still True every call


@pytest.mark.usefixtures("fake_redis")
async def test_once_notifies_first_time_only_same_day():
    alert = _FakeAlert(id=uuid.uuid4(), frequency="once")
    now = datetime(2026, 9, 15, 10, 0)

    assert await should_notify(alert, _signal(), now) is True
    assert await should_notify(alert, _signal(), now) is False


@pytest.mark.usefixtures("fake_redis")
async def test_dedupe_is_scoped_per_symbol_and_trigger_type():
    alert = _FakeAlert(id=uuid.uuid4(), frequency="once")
    now = datetime(2026, 9, 15, 10, 0)

    assert await should_notify(alert, _signal("RELIANCE"), now) is True
    assert await should_notify(alert, _signal("TCS"), now) is True  # different symbol, not deduped


@pytest.mark.usefixtures("fake_redis")
async def test_dedupe_resets_on_a_new_day():
    alert = _FakeAlert(id=uuid.uuid4(), frequency="once")
    day1 = datetime(2026, 9, 15, 10, 0)
    day2 = datetime(2026, 9, 16, 10, 0)

    assert await should_notify(alert, _signal(), day1) is True
    assert await should_notify(alert, _signal(), day2) is True
