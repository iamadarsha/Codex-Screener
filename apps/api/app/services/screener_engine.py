"""Main screener execution engine.

Loads universe symbols from Redis, batch-fetches indicator hashes via
pipeline, evaluates conditions, and returns matches -- optimised for
sub-1.5 s on 500 symbols.
"""

from __future__ import annotations

import hashlib
import json
import time
from decimal import Decimal, InvalidOperation
from typing import Any

import structlog

from app.services.condition_evaluator import (
    Condition,
    evaluate_conditions,
)
from app.services.orb import ORBDetector
from app.services.pattern_detector import detect_patterns
from app.services.prebuilt_scans import ScanDefinition, get_scan_by_id
from app.services.redis_cache import get_redis
from app.utils.redis_keys import (
    indicator_key,
    ltp_symbol_key,
    orb_range_key,
    scan_result_key,
    universe_key,
)

log = structlog.get_logger(__name__)

_SCAN_RESULT_TTL: int = 30  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_decimal(value: object) -> Decimal | None:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _scan_hash(scan_def: ScanDefinition, universe: str) -> str:
    """Deterministic hash of a scan definition for cache keying."""
    payload = json.dumps(
        {
            "id": scan_def.get("id", ""),
            "conditions": str(scan_def.get("conditions", [])),
            "pattern": scan_def.get("pattern", ""),
            "universe": universe,
            "timeframe": scan_def.get("timeframe", "1d"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _enrich_symbol_data(
    data: dict[str, str | None],
    orb_data: dict[str, str] | None = None,
) -> dict[str, str | None]:
    """Inject synthetic / derived fields that prebuilt scans expect.

    Mutations are applied **in-place** for performance (called per symbol).
    """
    # -- bollinger_width_pct ---------------------------------------------------
    bb_upper = _to_decimal(data.get("bollinger_upper"))
    bb_lower = _to_decimal(data.get("bollinger_lower"))
    sma_20 = _to_decimal(data.get("sma_20"))  # used as BB mid approximation
    if bb_upper is not None and bb_lower is not None and sma_20 and sma_20 != 0:
        data["bollinger_mid"] = str(sma_20)
        data["bollinger_width_pct"] = str((bb_upper - bb_lower) / sma_20)

    # -- volume_sma_20 (2x threshold) -----------------------------------------
    vol_sma = _to_decimal(data.get("sma_20_volume"))
    if vol_sma is not None:
        data["volume_sma_20"] = str(vol_sma * 2)

    # -- high_52w_95 -----------------------------------------------------------
    high_52w = _to_decimal(data.get("high_52w"))
    if high_52w is not None:
        data["high_52w_95"] = str(high_52w * Decimal("0.95"))

    # -- ORB range fields ------------------------------------------------------
    if orb_data:
        data["orb_high"] = orb_data.get("high")
        data["orb_low"] = orb_data.get("low")

    return data


# ---------------------------------------------------------------------------
# ScreenerEngine
# ---------------------------------------------------------------------------

class ScreenerEngine:
    """Execute scans against the live indicator store in Redis."""

    def __init__(self) -> None:
        self._redis = get_redis()
        self._orb = ORBDetector()

    # ------------------------------------------------------------------
    # Core scan runner
    # ------------------------------------------------------------------

    async def run_scan(
        self,
        scan_definition: ScanDefinition,
        universe: str = "nifty500",
    ) -> list[dict[str, Any]]:
        """Execute a scan and return matching symbols with their data.

        Parameters
        ----------
        scan_definition:
            A dict with at least ``conditions`` (list of
            :class:`Condition`) and optionally ``pattern``, ``timeframe``,
            ``meta``.
        universe:
            Redis set name (without prefix) -- ``"nifty50"`` or
            ``"nifty500"``.

        Returns
        -------
        list[dict]
            Each entry: ``{"symbol": str, "data": dict, "patterns": list}``.
        """
        t0 = time.perf_counter()

        # --- check cache ------------------------------------------------------
        cache_key = scan_result_key(_scan_hash(scan_definition, universe))
        cached = await self._redis.get(cache_key)
        if cached:
            log.info("scan_cache_hit", cache_key=cache_key)
            return json.loads(cached)

        # --- load universe ----------------------------------------------------
        symbols: set[str] = await self._redis.smembers(universe_key(universe))
        if not symbols:
            log.warning("scan_empty_universe", universe=universe)
            return []

        symbol_list = sorted(symbols)
        timeframe: str = scan_definition.get("timeframe", "1d")
        conditions: list[Condition] = scan_definition.get("conditions", [])
        pattern_name: str | None = scan_definition.get("pattern")

        # --- batch fetch indicators (pipeline) --------------------------------
        pipe = self._redis.pipeline(transaction=False)
        for sym in symbol_list:
            pipe.hgetall(indicator_key(sym, timeframe))
        indicator_results: list[dict[str, str]] = await pipe.execute()

        # --- optionally fetch ORB data (only for ORB scans) -------------------
        orb_map: dict[str, dict[str, str]] = {}
        needs_orb = any(
            (
                getattr(c.left, "name", "") in ("orb_high", "orb_low")
                or getattr(c.right, "name", "") in ("orb_high", "orb_low")
            )
            for c in conditions
        )
        if needs_orb:
            orb_pipe = self._redis.pipeline(transaction=False)
            for sym in symbol_list:
                orb_pipe.hgetall(orb_range_key(sym))
            orb_results: list[dict[str, str]] = await orb_pipe.execute()
            for sym, orb_data in zip(symbol_list, orb_results):
                if orb_data:
                    orb_map[sym] = orb_data

        # --- evaluate ---------------------------------------------------------
        matches: list[dict[str, Any]] = []

        for sym, raw_data in zip(symbol_list, indicator_results):
            if not raw_data:
                continue

            data = _enrich_symbol_data(raw_data, orb_map.get(sym))

            # condition-based matching
            if conditions:
                if not evaluate_conditions(conditions, data, logic="AND"):
                    continue

            # pattern-based matching
            if pattern_name:
                # Build minimal candle list from the indicator hash.
                # The hash should contain open/high/low/close for the latest
                # candle plus prev_open, prev_high, prev_low, prev_close for
                # the prior candle.
                candles = _build_candle_list(data)
                detected = detect_patterns(candles)
                if pattern_name not in detected:
                    continue

            # If neither conditions nor pattern are specified we skip the
            # symbol (a scan must have at least one filter).
            if not conditions and not pattern_name:
                continue

            matches.append(
                {
                    "symbol": sym,
                    "data": {k: v for k, v in data.items() if v is not None},
                    "patterns": (
                        detect_patterns(_build_candle_list(data))
                        if pattern_name
                        else []
                    ),
                }
            )

        # --- sort by relevance (RSI distance from extreme, volume ratio, etc.)
        matches.sort(key=lambda m: m["symbol"])

        # --- cache results ----------------------------------------------------
        await self._redis.set(
            cache_key,
            json.dumps(matches),
            ex=_SCAN_RESULT_TTL,
        )

        elapsed = time.perf_counter() - t0
        log.info(
            "scan_complete",
            scan_id=scan_definition.get("id", "custom"),
            universe=universe,
            symbols_checked=len(symbol_list),
            matches=len(matches),
            elapsed_ms=round(elapsed * 1000, 1),
        )

        return matches

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    async def run_prebuilt_scan(
        self,
        scan_id: str,
        universe: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run one of the 12 prebuilt scans by its id.

        Raises ``ValueError`` if *scan_id* is unknown.
        """
        scan_def = get_scan_by_id(scan_id)
        if scan_def is None:
            raise ValueError(f"Unknown prebuilt scan: {scan_id!r}")
        univ = universe or scan_def.get("universe", "nifty500")
        return await self.run_scan(scan_def, universe=univ)

    async def run_custom_scan(
        self,
        conditions: list[Condition],
        universe: str = "nifty500",
        timeframe: str = "1d",
        pattern: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build an ad-hoc scan definition and execute it."""
        scan_def: ScanDefinition = {
            "id": "custom",
            "conditions": conditions,
            "timeframe": timeframe,
        }
        if pattern:
            scan_def["pattern"] = pattern
        return await self.run_scan(scan_def, universe=universe)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_candle_list(data: dict[str, str | None]) -> list[dict[str, Any]]:
    """Construct a chronological candle list from indicator hash fields.

    Expects keys like ``open``, ``high``, ``low``, ``close`` for the current
    candle and ``prev_open``, ``prev_high``, ``prev_low``, ``prev_close`` for
    the previous candle.
    """
    candles: list[dict[str, Any]] = []

    # Previous candle
    prev = {}
    for field in ("open", "high", "low", "close", "volume"):
        val = data.get(f"prev_{field}")
        if val is not None:
            prev[field] = val
    if len(prev) >= 4:  # need at least OHLC
        candles.append(prev)

    # Current candle
    curr = {}
    for field in ("open", "high", "low", "close", "volume"):
        val = data.get(field)
        if val is not None:
            curr[field] = val
    if len(curr) >= 4:
        candles.append(curr)

    return candles
