"""Research run lifecycle status.

A plain enum — no transition-validation state machine. `replay.py` and
`store.py` only ever move a run forward along the natural
CREATED -> VALIDATING -> RUNNING -> (SUCCEEDED | FAILED | CANCELLED) path;
there is no separate `EVIDENCE_INVALID` state, per the approved plan's own
"only if it materially simplifies" clause — an evidence-invalid run is a
`FAILED` run whose `evidence.json` carries the detail.
"""

from __future__ import annotations

from enum import Enum


class RunStatus(str, Enum):
    CREATED = "created"
    VALIDATING = "validating"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
