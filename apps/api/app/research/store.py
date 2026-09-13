"""Local-filesystem persistence for research run artifacts.

Every read/write goes through `app.research.artifacts`'s safe path
resolution (`resolve_run_dir`) and atomic writes (`atomic_write_json`) — no
method here ever accepts or constructs a raw filesystem path itself.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.research.artifacts import atomic_write_json, read_json, resolve_run_dir
from app.research.replay import build_scan_hash
from app.research.run_manifest import RunManifest
from app.research.run_state import RunStatus
from app.utils.time import now_ist


class ResearchRunStore:
    """Reads/writes `manifest.json`, `request.json`, `state.json`,
    `evidence.json`, and `results.json` under
    `<research_runs_root>/<run_id>/`.
    """

    def create_run(
        self,
        scan_definition: dict[str, Any],
        universe: str,
        as_of: datetime,
        timeframe: str,
    ) -> RunManifest:
        """Create a new run: generate its id, write `manifest.json` +
        `request.json` + an initial CREATED `state.json`, and return the
        manifest.
        """
        created_at = now_ist()
        run_id = f"{created_at:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
        scan_hash = build_scan_hash(scan_definition)

        manifest = RunManifest(
            run_id=run_id,
            created_at=created_at,
            as_of=as_of,
            universe=universe,
            scan_hash=scan_hash,
            timeframe=timeframe,
            status=RunStatus.CREATED,
        )

        run_dir = resolve_run_dir(run_id)
        atomic_write_json(run_dir / "manifest.json", manifest.model_dump(mode="json"))
        atomic_write_json(
            run_dir / "request.json",
            {
                "scan_definition": _json_safe(scan_definition),
                "universe": universe,
                "as_of": as_of.isoformat(),
                "timeframe": timeframe,
            },
        )
        atomic_write_json(
            run_dir / "state.json",
            {"status": RunStatus.CREATED.value, "updated_at": created_at.isoformat()},
        )
        return manifest

    def update_state(
        self,
        run_id: str,
        status: RunStatus,
        extra: dict[str, Any] | None = None,
    ) -> None:
        run_dir = resolve_run_dir(run_id)
        state: dict[str, Any] = {
            "status": status.value,
            "updated_at": now_ist().isoformat(),
        }
        if extra:
            state.update(extra)
        atomic_write_json(run_dir / "state.json", state)

    def read_manifest(self, run_id: str) -> RunManifest | None:
        run_dir = resolve_run_dir(run_id)
        data = read_json(run_dir / "manifest.json")
        if data is None:
            return None
        return RunManifest.model_validate(data)

    def read_state(self, run_id: str) -> dict[str, Any] | None:
        run_dir = resolve_run_dir(run_id)
        return read_json(run_dir / "state.json")

    def read_evidence(self, run_id: str) -> dict[str, Any] | None:
        run_dir = resolve_run_dir(run_id)
        return read_json(run_dir / "evidence.json")

    def write_evidence(self, run_id: str, evidence: dict[str, Any]) -> None:
        run_dir = resolve_run_dir(run_id)
        atomic_write_json(run_dir / "evidence.json", evidence)

    def write_results(self, run_id: str, results: dict[str, Any]) -> None:
        run_dir = resolve_run_dir(run_id)
        atomic_write_json(run_dir / "results.json", results)

    def read_results(self, run_id: str) -> dict[str, Any] | None:
        run_dir = resolve_run_dir(run_id)
        return read_json(run_dir / "results.json")


def _json_safe(value: Any) -> Any:
    """Best-effort JSON-safe projection for `request.json` (diagnostic
    only — `manifest.json`/`evidence.json`/`results.json` carry the data
    that actually matters). Falls back to `repr()` for anything that
    doesn't round-trip cleanly (e.g. a `dsl_root` `BoolNode`)."""
    import json

    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {k: _json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        return repr(value)
