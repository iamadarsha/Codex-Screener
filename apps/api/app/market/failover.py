"""Primary/fallback state machine for the realtime price feed.

Upstox V3 is meant to be the primary feed once live (master prompt: "Do not
make NSE scraping the primary realtime spine when a documented websocket
feed exists"). `nse_poller.py`'s existing 30s REST poll is kept as the
fallback, started when the primary feed goes stale and stopped once it
recovers (master prompt §46: "If Upstox fails: reconnect, backoff,
resubscribe, mark stale, fallback if configured").

This class only tracks the *decision* — wiring it to actually start/stop
`nse_poller_loop` happens in provider.py during Milestone 2.2, once a live
Upstox connection exists to test failover against for real. The state
machine's transition logic itself is fully unit-testable without one (see
apps/api/app/tests/test_failover.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class FeedStatus(str, Enum):
    PRIMARY_LIVE = "primary_live"
    DEGRADED = "degraded"
    FALLBACK = "fallback"
    RECOVERING = "recovering"


@dataclass
class FailoverConfig:
    degraded_after_seconds: float = 10.0
    fallback_after_seconds: float = 30.0
    recovery_confirm_seconds: float = 5.0


class FailoverController:
    """Tracks primary-feed health and decides when to fall back / recover.

    Call `record_primary_tick()` whenever a tick arrives from the primary
    feed, and `evaluate(now)` periodically to get the current `FeedStatus`.
    """

    def __init__(self, config: FailoverConfig | None = None) -> None:
        self._config = config or FailoverConfig()
        self._status = FeedStatus.PRIMARY_LIVE
        self._last_primary_tick: float | None = None
        self._recovering_since: float | None = None

    @property
    def status(self) -> FeedStatus:
        return self._status

    @property
    def has_ever_ticked(self) -> bool:
        """False until the very first primary tick arrives.

        Distinct from `status`/`should_run_fallback_poller()`: those treat
        "no tick has ever arrived" as a fresh start rather than staleness
        (see `evaluate()`), which is correct for the controller's own
        transition logic but wrong as the sole signal for "should a
        fallback data source run" — a primary that has never once proven
        itself live (e.g. still connecting, or started while markets are
        closed) shouldn't be trusted over a working fallback just because
        it hasn't technically gone *stale* yet.
        """
        return self._last_primary_tick is not None

    def record_primary_tick(self, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        self._last_primary_tick = now
        if self._status in (FeedStatus.DEGRADED, FeedStatus.FALLBACK):
            if self._recovering_since is None:
                self._recovering_since = now
            self._status = FeedStatus.RECOVERING

    def evaluate(self, now: float | None = None) -> FeedStatus:
        now = now if now is not None else time.monotonic()

        if self._status == FeedStatus.RECOVERING:
            if (
                self._recovering_since is not None
                and now - self._recovering_since >= self._config.recovery_confirm_seconds
            ):
                self._status = FeedStatus.PRIMARY_LIVE
                self._recovering_since = None
            return self._status

        if self._last_primary_tick is None:
            # No primary tick has ever arrived — fresh start, not stale.
            return self._status

        silence = now - self._last_primary_tick
        if silence >= self._config.fallback_after_seconds:
            self._status = FeedStatus.FALLBACK
            self._recovering_since = None
        elif silence >= self._config.degraded_after_seconds:
            if self._status == FeedStatus.PRIMARY_LIVE:
                self._status = FeedStatus.DEGRADED

        return self._status

    def should_run_fallback_poller(self) -> bool:
        return self._status in (FeedStatus.DEGRADED, FeedStatus.FALLBACK)
