from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReplayScanCondition(BaseModel):
    """Legacy flat condition shape — same fields as `screener.ScanCondition`,
    duplicated here so `app/research/` has no import dependency on the live
    screener's request schemas."""

    indicator: str
    operator: str
    value: float | str | None = None


class ReplayRequest(BaseModel):
    universe: str = "nifty500"
    conditions: list[ReplayScanCondition] = Field(default_factory=list)
    # Nested DSL tree (same raw-dict shape `CustomScanRequest.dsl` accepts) —
    # takes precedence over `conditions` when both are present.
    dsl: dict[str, object] | None = None
    pattern: str | None = None
    as_of: datetime
    timeframe: str = "1d"


class ReplayCreatedOut(BaseModel):
    run_id: str
    status: str


class RunStateOut(BaseModel):
    run_id: str
    manifest: dict[str, Any]
    state: dict[str, Any]


class RunEvidenceOut(BaseModel):
    run_id: str
    evidence: dict[str, Any]


class RunResultsOut(BaseModel):
    run_id: str
    valid: bool
    message: str | None = None
    evidence: dict[str, Any] | None = None
    results: dict[str, Any] | None = None
