"""`RunManifest` — the immutable record of what a research run was asked to
do, written once at run creation (`ResearchRunStore.create_run`).
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.research.run_state import RunStatus


def get_code_version() -> str:
    """Return the current git commit SHA, or ``"unknown"`` if unavailable.

    A container image may not have `.git` mounted, or `git` itself may not
    be on PATH — either should degrade gracefully rather than crash a
    replay run, since `code_version` is provenance metadata, not something
    the replay's correctness depends on.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            sha = result.stdout.strip()
            if sha:
                return sha
        return "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


class RunManifest(BaseModel):
    """What a research run was asked to do — written once, never mutated."""

    run_id: str
    run_type: Literal["scan_replay"] = "scan_replay"
    created_at: datetime
    as_of: datetime
    universe: str
    scan_hash: str
    timeframe: str
    timezone: str = "Asia/Kolkata"
    code_version: str = Field(default_factory=get_code_version)
    data_source: list[str] = Field(default_factory=lambda: ["stored_1m"])
    status: RunStatus = RunStatus.CREATED
