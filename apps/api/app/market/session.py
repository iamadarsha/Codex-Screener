"""NSE session (market-hours) tracking.

Time-window logic here is a fallback/reference for tests and for candle
boundary math when no live feed is connected. Once the V3 feed is live,
`SessionTracker.update_from_market_info` should be treated as authoritative
over the time-window heuristic — Upstox's own `market_info` message reports
real segment/session status directly (including pre-open and Closing
Auction Session windows), so there's no need to reimplement exchange-hours
logic from scratch (master prompt §22).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.utils.time import IST, is_market_open, now_ist


@dataclass
class SessionTracker:
    """Tracks live market-session status for one exchange segment.

    Holiday handling is intentionally pluggable rather than a hardcoded
    date list — NSE's holiday calendar changes yearly, and hardcoding it
    here risks silently going stale. Pass a `holidays` set of `date`
    objects sourced from NSE's published calendar when available.
    """

    holidays: set[date] = field(default_factory=set)
    _segment_status: dict[str, str] = field(default_factory=dict, init=False)
    _last_market_info_ts: int | None = field(default=None, init=False)

    def update_from_market_info(self, segment_status: dict[str, str], current_ts: int) -> None:
        """Update live status from the feed's own `market_info` message — authoritative."""
        self._segment_status = dict(segment_status)
        self._last_market_info_ts = current_ts

    def is_regular_session_live(self, segment: str = "NSE_EQ") -> bool:
        """True if the live feed reports this segment as in its normal open session."""
        return self._segment_status.get(segment) == "NORMAL_OPEN"

    def has_live_status(self) -> bool:
        return self._last_market_info_ts is not None

    def is_market_open_heuristic(self, dt: datetime | None = None) -> bool:
        """Time-window + holiday fallback, used when no live market_info is available yet."""
        candidate = dt or now_ist()
        if candidate.astimezone(IST).date() in self.holidays:
            return False
        return is_market_open(candidate)

    def session_date(self, dt: datetime | None = None) -> date:
        """The trading-session date, for VWAP/candle-boundary reset purposes."""
        candidate = dt or now_ist()
        return candidate.astimezone(IST).date()
