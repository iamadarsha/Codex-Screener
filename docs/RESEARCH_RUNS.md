# Research Runs — Evidence-Gated Scan/Pattern Replay

A minimal, BreakoutScan-native run-lifecycle + evidence system for historical scan/pattern replay, inspired by the run-lifecycle *concept* in Vibe-Trading's `state.py`/`backtest_tool.py` (MIT-licensed) — no Vibe-Trading code, runner, MCP server, or backtest engine was ported.

## Scope (v1)

This integration builds **scan/DSL + pattern replay only**. It answers: *"What would this scan have shown as of some past timestamp?"* It does **not** build a strategy backtest (P&L, fills, position sizing, equity curve) — that's a materially different, larger feature, deliberately out of scope per the approved plan. It also does not replay the breakout-lifecycle state machine (ARMED→TRIGGERED→CONFIRMED) — that needs its own isolated tracker store and session-open parameterization, deferred to a future round.

## Architecture

```
POST /api/research/replay
    │
    ▼
ResearchRunStore.create_run()  → manifest.json, request.json, state.json (CREATED)
    │
    ▼ (FastAPI BackgroundTasks)
replay_scan()
    │
    ├─ fetch_candle_history_as_of(symbol, timeframe, as_of)   [new, additive, in app/market/candles.py]
    ├─ fresh SymbolIndicatorState() per symbol, replayed bar-by-bar via .update(candle)
    ├─ EvalContext(...) → evaluate() [DSL]  /  evaluate_conditions() [legacy]  /  detect_patterns()
    │      ^ all three are pre-existing, UNMODIFIED, pure functions — replay does not fork scan logic
    └─ validate_evidence(...)
    │
    ▼
ResearchRunStore.write_evidence() / write_results() / update_state(SUCCEEDED|FAILED)
```

Run artifacts live under `research_runs/<YYYYMMDD_HHMMSS>_<short-id>/` (path configurable via `settings.research_runs_root`, default `./research_runs`) — local filesystem, not a database or object storage, per the approved plan (no R2 implementation exists yet in this repo; a DB migration for this would be premature).

## API

- `POST /api/research/replay` — body: `universe` (`nifty50`/`nifty500`/`fno`/other→all active), `as_of` (datetime), `timeframe`, and one of `conditions` (legacy flat), `dsl` (DSL scan), or `pattern`. Returns `202 {run_id, status: "created"}` immediately; the replay itself runs in the background.
- `GET /api/research/runs/{run_id}` — manifest + current lifecycle state.
- `GET /api/research/runs/{run_id}/evidence` — the evidence record.
- `GET /api/research/runs/{run_id}/results` — results, with `valid: false` and the message *"Historical replay unavailable: evidence validation failed."* if evidence status is `invalid` — the raw data is still returned for diagnostics but never presented as a trustworthy finding.

A malformed or path-traversal-attempt `run_id` is rejected with `400`, never resolved outside `research_runs_root` — see `resolve_run_dir()` in `app/research/artifacts.py`.

## Run lifecycle

`CREATED → RUNNING → SUCCEEDED | FAILED` (no separate `CANCELLED`/`EVIDENCE_INVALID` state machine complexity — an invalid-evidence run lands in `FAILED`, with the detail in its evidence record).

See `docs/POINT_IN_TIME.md` for the evidence-gating contract itself, and `apps/api/app/tests/test_research_*.py` for the full test matrix (state, manifest/atomic-writes, evidence truth table, end-to-end replay, future-leakage regression, determinism, route safety).
