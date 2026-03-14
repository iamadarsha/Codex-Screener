from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.common import ErrorResponse
from app.schemas.screener import (
    CustomScanRequest,
    PrebuiltScanOut,
    ScanRequest,
    ScanResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screener", tags=["screener"])


async def _enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    """Enrich a scan result item with indicator data from Redis."""
    from app.services.redis_cache import hget_all
    from app.utils.redis_keys import indicator_key

    symbol = item.get("symbol", "")
    if not symbol:
        return item

    try:
        ind_key = indicator_key(symbol, "1d")
        indicators = await hget_all(ind_key)
        if not indicators:
            return item

        # RSI 14
        rsi_raw = indicators.get("rsi_14")
        if rsi_raw is not None:
            try:
                item["rsi_14"] = round(float(rsi_raw), 2)
            except (ValueError, TypeError):
                pass

        # EMA status: bullish if ema_9 > ema_21
        ema_9_raw = indicators.get("ema_9")
        ema_21_raw = indicators.get("ema_21")
        if ema_9_raw is not None and ema_21_raw is not None:
            try:
                ema_9 = float(ema_9_raw)
                ema_21 = float(ema_21_raw)
                item["ema_status"] = "Bullish" if ema_9 > ema_21 else "Bearish"
            except (ValueError, TypeError):
                pass

        # Volume
        vol_raw = indicators.get("volume")
        if vol_raw is not None:
            try:
                item["volume"] = float(vol_raw)
            except (ValueError, TypeError):
                pass

        # Signal strength from score if available in engine data
        if item.get("score") is not None:
            item["signal_strength"] = item["score"]

    except Exception as e:
        logger.debug("enrich_item_failed symbol=%s error=%s", symbol, e)

    return item


async def _enrich_items(items: list[dict[str, Any]], conditions: list[str] | None = None) -> list[dict[str, Any]]:
    """Enrich a list of scan result items with indicator data."""
    enriched = []
    for item in items:
        item = await _enrich_item(item)
        if conditions:
            item["matched_conditions"] = conditions
        enriched.append(item)
    return enriched


@router.get("/prebuilt", response_model=list[PrebuiltScanOut])
async def list_prebuilt_scans():
    """Return all available prebuilt scans."""
    try:
        from app.services.prebuilt_scans import get_prebuilt_scans

        scans = get_prebuilt_scans()
        out = []
        for s in scans:
            # Convert Condition dataclasses to dicts for Pydantic serialization
            s_copy = dict(s)
            if "conditions" in s_copy and s_copy["conditions"]:
                from dataclasses import asdict, fields

                s_copy["conditions"] = [
                    asdict(c) if hasattr(c, "__dataclass_fields__") else c
                    for c in s_copy["conditions"]
                ]
            out.append(PrebuiltScanOut(**s_copy))
        return out
    except Exception as exc:
        logger.exception("Failed to load prebuilt scans")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/run", response_model=ScanResult)
async def run_prebuilt_scan(req: ScanRequest):
    """Run a prebuilt scan by ID and return matching symbols."""
    try:
        from app.services.prebuilt_scans import get_scan_by_id
        from app.services.screener_engine import ScreenerEngine

        scan_def = get_scan_by_id(req.scan_id)
        if not scan_def:
            raise HTTPException(
                status_code=404, detail=f"Scan '{req.scan_id}' not found"
            )

        engine = ScreenerEngine()
        results = await engine.run_prebuilt_scan(
            scan_id=req.scan_id,
            universe=req.universe,
        )

        # Extract condition names from scan definition (Condition dataclasses)
        condition_names = []
        for c in (scan_def.get("conditions") or []):
            if hasattr(c, "left") and hasattr(c.left, "name"):
                condition_names.append(c.left.name)
            elif isinstance(c, dict):
                condition_names.append(c.get("indicator", c.get("name", "")))

        # Transform engine results to ScanResultItem format
        items = []
        for r in results:
            data = r.get("data", {})
            items.append({
                "symbol": r.get("symbol", ""),
                "company_name": r.get("symbol", ""),
                "ltp": float(data.get("close", 0) or 0),
                "change_pct": float(data.get("change_pct", 0) or 0),
                "sector": data.get("sector", ""),
                "matched_conditions": condition_names if condition_names else [],
                "score": float(data.get("score", 0) or 0) if data.get("score") else None,
            })

        # Enrich with indicator data from Redis
        items = await _enrich_items(items)

        return ScanResult(
            scan_id=req.scan_id,
            scan_name=scan_def.get("name", req.scan_id),
            description=scan_def.get("description"),
            run_at=datetime.now(timezone.utc),
            total_matches=len(items),
            items=items,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Scan run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/custom", response_model=ScanResult)
async def run_custom_scan(req: CustomScanRequest):
    """Run a custom scan with user-defined conditions."""
    try:
        from app.services.screener_engine import ScreenerEngine

        engine = ScreenerEngine()
        conditions_raw = [c.model_dump() for c in req.conditions]
        results = await engine.run_custom_scan(
            conditions=conditions_raw,
            universe=req.universe,
            timeframe=req.timeframe,
        )

        # Extract condition names from user-defined conditions
        condition_names = [
            c.get("indicator", "")
            for c in conditions_raw
            if c.get("indicator")
        ]

        # Transform engine results to ScanResultItem format
        items = []
        for r in results:
            data = r.get("data", {})
            items.append({
                "symbol": r.get("symbol", ""),
                "company_name": r.get("symbol", ""),
                "ltp": float(data.get("close", 0) or 0),
                "change_pct": float(data.get("change_pct", 0) or 0),
                "sector": data.get("sector", ""),
                "matched_conditions": condition_names if condition_names else [],
                "score": float(data.get("score", 0) or 0) if data.get("score") else None,
            })

        # Enrich with indicator data from Redis
        items = await _enrich_items(items)

        return ScanResult(
            scan_id="custom",
            scan_name=req.name or "Custom Scan",
            run_at=datetime.now(timezone.utc),
            total_matches=len(items),
            items=items,
        )
    except Exception as exc:
        logger.exception("Custom scan failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/results/{scan_id}", response_model=ScanResult)
async def get_cached_results(scan_id: str):
    """Get cached scan results by scan ID."""
    try:
        from app.services.redis_cache import get_json

        cached = await get_json(f"scan_result:{scan_id}")
        if not cached:
            raise HTTPException(
                status_code=404, detail=f"No cached results for scan '{scan_id}'"
            )
        return ScanResult(**cached)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch cached results")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
