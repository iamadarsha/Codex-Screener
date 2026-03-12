"""IST timezone helpers and market-hours utilities."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

# IST is UTC+05:30
IST = timezone(timedelta(hours=5, minutes=30))

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

# Supported candle timeframe widths in minutes
_TF_MINUTES: dict[str, int] = {
    "1min": 1,
    "5min": 5,
    "15min": 15,
}


def now_ist() -> datetime:
    """Return the current datetime in IST."""
    return datetime.now(tz=IST)


def is_market_open(dt: datetime | None = None) -> bool:
    """Return ``True`` if *dt* (or now) falls within NSE regular trading hours.

    Only checks the time window; does **not** account for holidays or weekends.
    """
    if dt is None:
        dt = now_ist()
    else:
        dt = dt.astimezone(IST)

    # Weekday check: Monday=0 .. Friday=4
    if dt.weekday() > 4:
        return False

    return MARKET_OPEN <= dt.time() <= MARKET_CLOSE


def get_candle_boundary(ts: datetime, timeframe: str) -> datetime:
    """Snap *ts* down to the nearest candle boundary for *timeframe*.

    For example, with ``timeframe='5min'`` a timestamp of 09:17:42 IST
    maps to 09:15:00 IST.

    Raises :class:`ValueError` for unknown timeframes.
    """
    minutes = _TF_MINUTES.get(timeframe)
    if minutes is None:
        raise ValueError(f"Unsupported timeframe: {timeframe!r}")

    ts_ist = ts.astimezone(IST)
    floored_minute = (ts_ist.minute // minutes) * minutes
    return ts_ist.replace(minute=floored_minute, second=0, microsecond=0)


def market_open_today() -> datetime:
    """Return today's market-open datetime (09:15 IST)."""
    today = now_ist().date()
    return datetime.combine(today, MARKET_OPEN, tzinfo=IST)


def market_close_today() -> datetime:
    """Return today's market-close datetime (15:30 IST)."""
    today = now_ist().date()
    return datetime.combine(today, MARKET_CLOSE, tzinfo=IST)
