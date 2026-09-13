"""Safe, atomic filesystem access for research run artifacts.

Every run's `manifest.json` / `request.json` / `state.json` / `evidence.json`
/ `results.json` lives under `settings.research_runs_root / <run_id>`.
`run_id` values ultimately originate from HTTP request paths (`GET
/api/research/runs/{run_id}`), so path safety here is the whole ballgame —
`resolve_run_dir` never trusts a regex alone (defense in depth: resolve the
path, then verify it is still a descendant of the configured root).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings

_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_MAX_RUN_ID_LENGTH = 128


def resolve_run_dir(run_id: str) -> Path:
    """Return the on-disk directory for *run_id*, validated and confined to
    `settings.research_runs_root`.

    Raises `ValueError` for anything that isn't a strict alnum/dash/
    underscore token — including any `..` or `/` sequence, even though the
    regex already excludes both; the resolve-and-check step below is the
    real defense, the regex is just a fast, readable first filter.
    """
    if not run_id or len(run_id) > _MAX_RUN_ID_LENGTH:
        raise ValueError(f"invalid run_id: {run_id!r}")
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise ValueError(f"invalid run_id: {run_id!r}")
    if not _RUN_ID_PATTERN.match(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")

    settings = get_settings()
    root = Path(settings.research_runs_root).resolve()
    candidate = (root / run_id).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"invalid run_id: {run_id!r} (escapes research_runs_root)") from exc

    return candidate


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write *data* as JSON to *path* atomically.

    Writes to a `.tmp` sibling in the same directory, `fsync`s it, then
    `os.replace()`s it into place — so a reader never observes a partially
    written file, and a crash mid-write leaves only the (untouched) old
    file or the (fully written) temp file, never a corrupt final file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def read_json(path: Path) -> dict[str, Any] | None:
    """Return the parsed JSON at *path*, or `None` if it doesn't exist."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
