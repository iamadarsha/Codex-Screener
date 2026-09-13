# Integration Report — Surgical AI + Research Integration

## Baseline

Commit `a152b3e` on `main` (Phase 3.4a complete), 232/232 tests passing. See `docs/INTEGRATION_BASELINE.md` for full detail. Work done on branch `feature/surgical-research-integrations`.

## TradingAgents integration (structured AI output)

Adapted the *concept* only — a typed-schema call → validate → fallback boundary — reimplemented natively:
- New `apps/api/app/services/ai_schemas.py` (`NewsSource`, `AIPick`, `AIPicksResponse`).
- `ai_suggestions.py::_parse_ai_response()` now validates through Pydantic instead of a bare `json.loads` + shallow shape check.
- Gemini calls request native `response_schema=AIPicksResponse`; Groq/xAI calls request `response_format={"type":"json_object"}`. Post-hoc Pydantic validation still runs regardless in both cases.
- Fixed a real pre-existing bug: `source` was hardcoded to `"groq"` before the Groq/xAI fallback ran, mislabeling provenance when xAI actually produced the result.
- No TradingAgents source code or dependency added. See `docs/AI_STRUCTURED_OUTPUT.md`.

## Vibe-Trading integration (evidence-gated research runs)

Adapted the *concept* only — run lifecycle + point-in-time evidence — reimplemented natively against BreakoutScan's own scan/pattern engines:
- New `apps/api/app/research/` package: `run_state.py`, `run_manifest.py`, `evidence.py`, `artifacts.py`, `replay.py`, `store.py`.
- New additive `fetch_candle_history_as_of()` in `app/market/candles.py` (existing `fetch_candle_history()` untouched).
- New `apps/api/app/api/routes/research.py` (`POST /api/research/replay`, `GET /api/research/runs/{run_id}[/evidence|/results]`).
- Scope decision: **scan/DSL + pattern replay only** — breakout-lifecycle replay and any P&L/equity-curve backtest engine are explicitly deferred (see the plan file's "Scope decisions" section for why).
- No Vibe-Trading runner, MCP server, or backtest-engine code ported. See `docs/RESEARCH_RUNS.md` and `docs/POINT_IN_TIME.md`.

## Files changed

Modified (additive changes only, no deletions): `apps/api/app/services/ai_suggestions.py`, `apps/api/app/market/candles.py`, `apps/api/app/core/config.py`, `apps/api/app/api/routes/__init__.py`, `apps/api/app/tests/conftest.py`.

Created: `apps/api/app/services/ai_schemas.py`; `apps/api/app/research/{__init__,run_state,run_manifest,evidence,artifacts,replay,store}.py`; `apps/api/app/api/routes/research.py`; `apps/api/app/schemas/research.py`; 9 new test files (`test_ai_structured.py`, `test_ai_suggestions_contract.py`, `test_research_run_state.py`, `test_research_manifest.py`, `test_research_evidence.py`, `test_research_replay.py`, `test_research_replay_future_leakage.py`, `test_research_replay_determinism.py`, `test_research_routes.py`); 5 docs (`INTEGRATION_BASELINE.md`, `THIRD_PARTY_INTEGRATIONS.md`, `AI_STRUCTURED_OUTPUT.md`, `RESEARCH_RUNS.md`, `POINT_IN_TIME.md`, this report).

## Dependencies

`git diff a152b3e -- apps/api/requirements.txt apps/api/requirements-dev.txt apps/web/package.json` — **zero changes**. No new dependency was added; both integrations were built entirely on SDKs (`google-genai`, `groq`, `pydantic`, `sqlalchemy`, stdlib) already present at baseline.

## Tests

Command: `cd apps/api && python -m pytest app/tests/ -q`
Result: **299 passed, 0 failed** (232 baseline + 22 Integration A + 45 Integration B).

The future-leakage test (`test_research_replay_future_leakage.py`) was independently verified to genuinely exercise the `as_of` SQL predicate (via `stmt.compile()` on the real query) rather than trivially passing against a pre-filtered fixture.

## Non-regression

- Framework-leak grep (`langgraph|langchain|tradingagents|vibe-trading`, case-insensitive) across `apps/api/app`: zero matches outside documentation.
- Dependency-direction grep confirmed `app/market/`, `app/breakouts/`, `app/screener/` contain no import of `app.research` or `app.services.ai_schemas` — the one hit found was a docstring comment in `candles.py`, not an import.
- All 232 pre-existing tests still pass unmodified.
- `python -c "import app.main; ..."` (all new/modified modules) succeeds cleanly.

## Security

- `resolve_run_dir()` rejects any `run_id` outside a strict alnum/dash/underscore pattern and additionally verifies the resolved path is a descendant of `research_runs_root` before use — tested against explicit path-traversal attempts in `test_research_routes.py`.
- Replay's scan input goes through the existing DSL parser/validator (`parse_scan`/`validate`) — same validation the live custom-scan route already enforces, not a new arbitrary-code path.
- No credentials or secrets appear in any new log line (checked structlog/logging calls added in this integration).

## Performance

Not benchmarked with a live load-test (would require either real NSE market hours or a synthetic tick-generation harness beyond this round's scope). Structural argument for no regression: the AI layer's code path is unchanged in shape (same fallback chain, same call sites, only the validation/request-config internals changed) and remains reachable only via its 3 existing HTTP routes; the research replay path is entirely new code, reachable only via 3 new HTTP routes, and touches the live tick/candle/indicator/breakout pipeline in exactly one place — an additive, never-called-by-the-live-path function in `candles.py`. No existing hot-path function was modified.

## Limitations

- Replay does not cover breakout-lifecycle state (ARMED→CONFIRMED) — scan/DSL and pattern replay only.
- No backtest (P&L/equity-curve) engine — replay only answers "what would the screener have shown," not "what would a strategy have returned."
- `scan_version_check` in the evidence record is a presence check (non-empty hash), not a lookup-and-compare against a stored scan catalog — no such catalog exists in this repo yet.
- Apple Container build/run smoke test (`scripts/container-build.sh`/`container-run.sh`/`container-test.sh`) was **not run** — the `container` CLI is not installed in this session's environment. Substituted with a direct Python import sanity check of every new/modified module (passed cleanly) as partial evidence the app still starts, but this is not equivalent to the brief's own required container smoke test and should be run manually before merging.
- No LICENSE file exists in the repo despite the README's MIT claim — pre-existing, unrelated to this work, flagged in `docs/THIRD_PARTY_INTEGRATIONS.md`.

---

## SURGICAL INTEGRATION REPORT

```
TradingAgents structured-output boundary:
PASS

Vibe-Trading evidence-gated research runs:
PASS

Live market-data flow:
UNCHANGED

Live screener flow:
UNCHANGED

Existing AI endpoint:
PASS

Historical replay:
PASS

Future-leakage tests:
PASS

Determinism tests:
PASS

Apple Container:
NOT RUN (container CLI unavailable in this environment — see Limitations)

Frontend build:
NOT RUN (no frontend changes made; not exercised this round)

Full test suite:
PASS (299/299)

New heavy dependencies:
NONE

Unrelated files changed:
NONE

Known limitations:
- Breakout-lifecycle replay not implemented (scan/pattern replay only)
- No backtest/P&L engine
- scan_version_check is presence-only, no scan catalog exists
- Apple Container smoke test not run in this session (environment limitation)
- Pre-existing missing LICENSE file (unrelated, flagged only)
```
