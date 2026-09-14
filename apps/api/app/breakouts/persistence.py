"""Durable side effects for a confirmed breakout signal.

This is the first real producer for the `alert_triggers` Redis channel
(`app/ws/alerts.py` has always subscribed to it, but nothing ever
published) and the first real writer of `AlertHistory` rows — completing
an existing half-built pipeline rather than building a new one.
"""

from __future__ import annotations

import json
import uuid

import structlog

from app.breakouts.types import BreakoutSignal
from app.db.session import SessionLocal
from app.services.redis_cache import publish

log = structlog.get_logger(__name__)

ALERT_TRIGGERS_CHANNEL = "alert_triggers"


def _conditions_met(signal: BreakoutSignal) -> list[dict[str, object]]:
    return [
        {
            "trigger_type": signal.trigger_type.value,
            "direction": signal.direction.value,
            "reference_level": float(signal.reference_level),
            "score": signal.score,
        }
    ]


async def publish_alert_trigger(alert_id: uuid.UUID, signal: BreakoutSignal) -> None:
    """Publish to `alert_triggers` in exactly the shape `app/ws/alerts.py`
    already relays: `{"alert_id","symbol","trigger_price","conditions_met"}`.
    """
    payload = {
        "alert_id": str(alert_id),
        "symbol": signal.symbol,
        "trigger_price": float(signal.trigger_price),
        "conditions_met": _conditions_met(signal),
    }
    await publish(ALERT_TRIGGERS_CHANNEL, json.dumps(payload, default=str))


async def record_alert_history(alert_id: uuid.UUID, signal: BreakoutSignal, session=None) -> None:
    """Accepts an optional caller-provided `session` so a single signal's
    whole persistence path (event + alert lookup + history) can share one
    connection checkout instead of opening a new one per call — see
    `app.breakouts.engine._handle_signal`. Falls back to its own session
    when called standalone (existing tests, ad-hoc use)."""
    from app.db.models.alert_history import AlertHistory

    async def _do(s) -> None:
        s.add(
            AlertHistory(
                alert_id=alert_id,
                symbol=signal.symbol,
                trigger_price=signal.trigger_price,
                conditions_met=_conditions_met(signal),
            )
        )
        await s.commit()

    if session is not None:
        await _do(session)
        return
    async with SessionLocal() as session:
        await _do(session)


async def record_breakout_event(signal: BreakoutSignal, session=None) -> None:
    """Same optional shared-`session` pattern as `record_alert_history`."""
    from app.db.models.breakout_event import BreakoutEvent

    async def _do(s) -> None:
        s.add(
            BreakoutEvent(
                symbol=signal.symbol,
                trigger_type=signal.trigger_type.value,
                direction=signal.direction.value,
                reference_level=signal.reference_level,
                trigger_price=signal.trigger_price,
                confirmation_price=signal.confirmation_price,
                score=signal.score,
                extra=signal.extra,
                triggered_at=signal.triggered_at,
                confirmed_at=signal.confirmed_at,
            )
        )
        await s.commit()

    if session is not None:
        await _do(session)
    else:
        async with SessionLocal() as session:
            await _do(session)
    log.info(
        "breakout_confirmed",
        symbol=signal.symbol,
        trigger_type=signal.trigger_type.value,
        direction=signal.direction.value,
        score=signal.score,
    )
