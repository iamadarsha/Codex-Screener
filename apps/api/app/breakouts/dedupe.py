"""Per-alert notification dedupe for confirmed (and failed) breakout signals."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.breakouts.types import BreakoutSignal
from app.services.redis_cache import get_redis
from app.utils.redis_keys import TTL_BREAKOUT_DEDUPE, breakout_dedupe_key

if TYPE_CHECKING:
    from app.db.models.alert import Alert


async def should_notify(alert: "Alert", signal: BreakoutSignal, now: datetime) -> bool:
    """True if *alert* should be notified for *signal* right now.

    `frequency="every_time"` always notifies. `"once"` and `"daily_digest"`
    both collapse to "first signal per symbol+trigger+outcome+day" for this
    round — a real digest batcher (aggregating multiple signals into one
    end-of-day email) is out of scope; this is a known, flagged simplification.
    The dedupe key is namespaced by `signal.status` so a FAILED (false
    breakout) signal is never suppressed by an earlier CONFIRMED dedupe entry
    for the same alert+symbol+trigger+day, or vice versa.
    """
    if alert.frequency == "every_time":
        return True

    key = breakout_dedupe_key(
        str(alert.id), signal.symbol, signal.trigger_type.value, now.date().isoformat(),
        outcome=signal.status.value,
    )
    redis = await get_redis()
    was_new = await redis.set(key, "1", nx=True, ex=TTL_BREAKOUT_DEDUPE)
    return bool(was_new)
