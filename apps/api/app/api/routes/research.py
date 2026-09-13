"""Evidence-gated historical scan/pattern replay API.

`POST /api/research/replay` kicks off a replay run in the background
(same `BackgroundTasks` convention as `ai_suggestions.py`) and returns
immediately with the new run's id; the remaining routes read back the
run's manifest/state/evidence/results from local-disk artifacts via
`ResearchRunStore`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.research.artifacts import resolve_run_dir
from app.research.replay import replay_scan
from app.research.run_state import RunStatus
from app.research.store import ResearchRunStore
from app.schemas.research import (
    ReplayCreatedOut,
    ReplayRequest,
    RunEvidenceOut,
    RunResultsOut,
    RunStateOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

_INVALID_EVIDENCE_MESSAGE = "Historical replay unavailable: evidence validation failed."


def _validate_run_id_or_400(run_id: str) -> None:
    """Reject a malformed/path-traversal-attempt `run_id` with a clean 4xx
    instead of letting `resolve_run_dir`'s `ValueError` propagate as a 500.
    """
    try:
        resolve_run_dir(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid run_id: {exc}") from exc


async def _resolve_universe_symbols(universe: str) -> list[str]:
    """Resolve a universe name to a symbol list directly from Postgres.

    Deliberately independent of the live Redis universe-set cache
    (`universe:{name}`, populated by the live poller) — a replay run must
    not depend on that cache being warm, per the approved plan's scope
    decision. `nifty50`/`nifty500`/`fno` map to the matching boolean column
    on `Stock`; anything else falls back to every active stock.
    """
    from sqlalchemy import select

    from app.db.models.stock import Stock
    from app.db.session import SessionLocal

    universe_lower = universe.lower()
    column_map = {
        "nifty50": Stock.is_nifty50,
        "nifty500": Stock.is_nifty500,
        "fno": Stock.is_fno,
    }
    filter_column = column_map.get(universe_lower)

    async with SessionLocal() as session:
        if filter_column is not None:
            stmt = select(Stock.symbol).where(filter_column.is_(True))
        else:
            stmt = select(Stock.symbol).where(Stock.is_active.is_(True))
        rows = (await session.execute(stmt)).scalars().all()
    return sorted(rows)


def _build_scan_definition(req: ReplayRequest) -> dict[str, Any]:
    """Build the plain-dict scan definition `replay_scan` expects, mirroring
    `screener.py::run_custom_scan`'s `dsl` vs `conditions` dispatch,
    simplified for replay's needs (no scan-id/meta bookkeeping)."""
    scan_definition: dict[str, Any] = {"timeframe": req.timeframe}

    if req.dsl is not None:
        from app.screener.dsl.parser import DslParseError, parse_scan
        from app.screener.dsl.validator import DslValidationError, validate

        try:
            dsl_root = parse_scan(req.dsl)
            validate(dsl_root, timeframe=req.timeframe)
        except (DslParseError, DslValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        scan_definition["dsl_root"] = dsl_root
    elif req.conditions:
        scan_definition["conditions"] = [c.model_dump() for c in req.conditions]

    if req.pattern:
        scan_definition["pattern"] = req.pattern

    if "dsl_root" not in scan_definition and "conditions" not in scan_definition and not req.pattern:
        raise HTTPException(
            status_code=422, detail="replay request must include 'conditions', 'dsl', or 'pattern'"
        )

    return scan_definition


async def _run_replay_background(
    run_id: str,
    scan_definition: dict[str, Any],
    universe_symbols: list[str],
    as_of,
    timeframe: str,
) -> None:
    """Runs `replay_scan` and writes evidence/results/final-state via the
    store — invoked as a FastAPI background task, never awaited by the
    request/response cycle."""
    store = ResearchRunStore()
    store.update_state(run_id, RunStatus.RUNNING)
    try:
        result = await replay_scan(
            run_id=run_id,
            scan_definition=scan_definition,
            universe_symbols=universe_symbols,
            as_of=as_of,
            timeframe=timeframe,
        )
        evidence = result.get("evidence", {})
        store.write_evidence(run_id, evidence)
        store.write_results(run_id, {k: v for k, v in result.items() if k != "evidence"})
        final_status = RunStatus.SUCCEEDED if result.get("status") == "SUCCEEDED" else RunStatus.FAILED
        store.update_state(run_id, final_status)
    except Exception as exc:  # noqa: BLE001 - background task must never raise unhandled
        logger.exception("replay_background_failed run_id=%s", run_id)
        store.update_state(run_id, RunStatus.FAILED, extra={"error": str(exc)})


@router.post("/replay", response_model=ReplayCreatedOut, status_code=202)
async def create_replay_run(req: ReplayRequest, background_tasks: BackgroundTasks):
    """Create a new replay run and kick it off in the background.

    Returns immediately with `{run_id, status}` — poll `GET
    /api/research/runs/{run_id}` for progress.
    """
    try:
        scan_definition = _build_scan_definition(req)
        universe_symbols = await _resolve_universe_symbols(req.universe)

        store = ResearchRunStore()
        manifest = store.create_run(
            scan_definition=scan_definition,
            universe=req.universe,
            as_of=req.as_of,
            timeframe=req.timeframe,
        )

        background_tasks.add_task(
            _run_replay_background,
            manifest.run_id,
            scan_definition,
            universe_symbols,
            req.as_of,
            req.timeframe,
        )

        return {"run_id": manifest.run_id, "status": "created"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_replay_run_failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=RunStateOut)
async def get_run(run_id: str):
    _validate_run_id_or_400(run_id)
    try:
        store = ResearchRunStore()
        manifest = store.read_manifest(run_id)
        if manifest is None:
            raise HTTPException(status_code=404, detail="run not found")
        state = store.read_state(run_id) or {}
        return {
            "run_id": run_id,
            "manifest": manifest.model_dump(mode="json"),
            "state": state,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_run_failed run_id=%s", run_id)
        raise HTTPException(status_code=500, detail="run manifest is corrupted or unreadable") from exc


@router.get("/runs/{run_id}/evidence", response_model=RunEvidenceOut)
async def get_run_evidence(run_id: str):
    _validate_run_id_or_400(run_id)
    try:
        store = ResearchRunStore()
        evidence = store.read_evidence(run_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="evidence not found for this run")
        return {"run_id": run_id, "evidence": evidence}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_run_evidence_failed run_id=%s", run_id)
        raise HTTPException(status_code=500, detail="evidence is corrupted or unreadable") from exc


@router.get("/runs/{run_id}/results", response_model=RunResultsOut)
async def get_run_results(run_id: str):
    _validate_run_id_or_400(run_id)
    try:
        store = ResearchRunStore()
        results = store.read_results(run_id)
        if results is None:
            raise HTTPException(status_code=404, detail="results not found for this run")

        evidence = store.read_evidence(run_id) or {}
        if evidence.get("status") == "invalid":
            return {
                "run_id": run_id,
                "valid": False,
                "message": _INVALID_EVIDENCE_MESSAGE,
                "evidence": evidence,
                # Retained for diagnostics only — never present as a valid finding.
                "results": results,
            }

        return {
            "run_id": run_id,
            "valid": True,
            "evidence": evidence,
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_run_results_failed run_id=%s", run_id)
        raise HTTPException(status_code=500, detail="results are corrupted or unreadable") from exc
