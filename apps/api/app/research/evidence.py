"""Point-in-time evidence gating for historical replay.

`validate_evidence` is the single correctness gate a replay run must pass
before its signals are allowed to be presented as trustworthy. It is a pure
function: no I/O, no wall-clock reads, no DB/Redis access — it only
inspects the candle data a replay already loaded plus the request
parameters, so it is fully unit-testable with synthetic fixtures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.utils.time import IST

EvidenceStatus = Literal["valid", "invalid", "incomplete"]


class EvidenceRecord(BaseModel):
    status: EvidenceStatus
    as_of: datetime
    max_market_timestamp_used: datetime | None = None
    future_data_detected: bool = False
    sources: list[dict[str, Any]] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


def _as_aware(dt: datetime) -> datetime:
    """Attach IST if *dt* is naive (daily bars serialize as date-only
    isoformat strings, which parse back as naive datetimes at midnight)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt


def _parse_ts(candle: dict[str, Any]) -> datetime | None:
    raw = candle.get("ts")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
    return None


def validate_evidence(
    candles_by_symbol: dict[str, list[dict[str, Any]]],
    as_of: datetime,
    universe_symbols: list[str],
    scan_hash: str,
) -> EvidenceRecord:
    """Run the four evidence checks against already-loaded historical data.

    Checks (all pure, no I/O):
      - `future_bar_check`: every candle's timestamp, across every symbol,
        must be `<= as_of`. This is defense-in-depth — `fetch_candle_history_as_of`
        already filters by `ts <= as_of` at the SQL layer — but a replay
        result should never be trusted on the strength of "the query should
        have filtered it" alone.
      - `timestamp_order_check`: each symbol's candle list must be in
        non-decreasing chronological order (a scrambled feed is exactly the
        kind of bug that silently produces confident-looking wrong signals).
      - `universe_check`: every symbol key present in `candles_by_symbol`
        must be a member of `universe_symbols`. One-directional by design —
        it catches a universe/data mismatch (data present for a symbol that
        was never part of the requested universe); it does NOT check the
        reverse (every universe symbol has data), since a universe symbol
        with zero candles is legitimately "incomplete", not "invalid".
      - `scan_version_check`: `scan_hash` is a non-empty string. This is a
        presence check only, not a lookup-and-compare check — confirming
        the hash actually matches a stored scan definition would require a
        DB lookup this function deliberately doesn't depend on (it must
        stay pure). Documented here rather than silently overclaimed.

    Overall `status`:
      - `"valid"` only if all four checks pass AND no symbol's candle list
        is empty.
      - `"invalid"` if any of the four checks fails (a genuine, load-bearing
        contradiction — future data, scrambled order, a universe mismatch,
        or a missing scan identity).
      - `"incomplete"` if all four checks pass but at least one symbol's
        candle list is empty (data simply isn't there yet — not a
        contradiction of the as-of cutoff, just nothing to evaluate).
    """
    universe_set = set(universe_symbols)
    errors: list[str] = []
    max_market_timestamp_used: datetime | None = None
    future_data_detected = False
    future_bar_check = True
    timestamp_order_check = True

    for symbol, candles in candles_by_symbol.items():
        prev_ts: datetime | None = None
        for candle in candles:
            ts = _parse_ts(candle)
            if ts is None:
                continue
            aware_ts = _as_aware(ts)

            if max_market_timestamp_used is None or aware_ts > max_market_timestamp_used:
                max_market_timestamp_used = aware_ts

            if aware_ts > _as_aware(as_of):
                future_bar_check = False
                future_data_detected = True
                errors.append(
                    f"{symbol}: candle timestamp {aware_ts.isoformat()} is after "
                    f"as_of cutoff {_as_aware(as_of).isoformat()}"
                )

            if prev_ts is not None and aware_ts < prev_ts:
                timestamp_order_check = False
                errors.append(
                    f"{symbol}: candle timestamps are not in chronological order "
                    f"({prev_ts.isoformat()} followed by {aware_ts.isoformat()})"
                )
            prev_ts = aware_ts

    universe_check = True
    for symbol in candles_by_symbol:
        if symbol not in universe_set:
            universe_check = False
            errors.append(f"{symbol}: present in replay data but not a member of the requested universe")

    scan_version_check = bool(scan_hash and scan_hash.strip())
    if not scan_version_check:
        errors.append(
            "scan_hash is empty — cannot confirm which scan definition produced "
            "this run (presence check only, not a lookup-and-compare check)"
        )

    has_missing_data = any(len(candles) == 0 for candles in candles_by_symbol.values())

    checks = {
        "future_bar_check": future_bar_check,
        "timestamp_order_check": timestamp_order_check,
        "universe_check": universe_check,
        "scan_version_check": scan_version_check,
    }

    status: EvidenceStatus
    if all(checks.values()) and not has_missing_data:
        status = "valid"
    elif not all(checks.values()):
        status = "invalid"
    else:
        status = "incomplete"

    sources = [
        {"symbol": symbol, "candle_count": len(candles)}
        for symbol, candles in candles_by_symbol.items()
    ]

    return EvidenceRecord(
        status=status,
        as_of=as_of,
        max_market_timestamp_used=max_market_timestamp_used,
        future_data_detected=future_data_detected,
        sources=sources,
        checks=checks,
        errors=errors,
    )
