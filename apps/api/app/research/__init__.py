"""Evidence-gated historical scan/pattern replay.

Surgical integration (see `docs/RESEARCH_RUNS.md` / `docs/POINT_IN_TIME.md`)
borrowing only the *concept* of run-lifecycle + point-in-time evidence
gating. No code is ported from any external repo — every module here is a
minimal, BreakoutScan-native implementation that reuses BreakoutScan's own
pure DSL/pattern/indicator primitives unmodified.

One-way dependency rule: this package depends on `app.market`,
`app.screener`, and `app.patterns` — never the other way around. Nothing in
those packages (or in `app.breakouts`) should ever import from
`app.research`.
"""

from __future__ import annotations
