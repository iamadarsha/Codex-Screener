from __future__ import annotations

import logging
from datetime import datetime, timezone

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


@router.get("/prebuilt", response_model=list[PrebuiltScanOut])
async def list_prebuilt_scans():
    """Return all available prebuilt scans."""
    try:
        from app.services.prebuilt_scans import get_prebuilt_scans

        scans = get_prebuilt_scans()
        return [PrebuiltScanOut(**s) for s in scans]
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

        return ScanResult(
            scan_id=req.scan_id,
            scan_name=scan_def.get("name", req.scan_id),
            description=scan_def.get("description"),
            run_at=datetime.now(timezone.utc),
            total_matches=len(results),
            items=results,
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
        results = await engine.run_custom_scan(
            conditions=[c.model_dump() for c in req.conditions],
            universe=req.universe,
            timeframe=req.timeframe,
        )

        return ScanResult(
            scan_id="custom",
            scan_name=req.name or "Custom Scan",
            run_at=datetime.now(timezone.utc),
            total_matches=len(results),
            items=results,
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
