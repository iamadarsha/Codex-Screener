# Point-in-Time Evidence Contract

A historical replay result is not trusted merely because code executed — it's trusted only when the engine can prove the run is valid and point-in-time safe.

## The property being enforced

For a replay `as_of` timestamp `T`, the scan/pattern evaluation must never see any bar with `timestamp > T`. This is enforced structurally, not by convention:

- `fetch_candle_history_as_of(symbol, timeframe, as_of)` (`app/market/candles.py`) issues a Postgres query with `WHERE ts <= :as_of` — the database itself never returns a future row. The pre-existing `fetch_candle_history()` (no cutoff, "most recent N as of now") is untouched and used only by the live pipeline.
- The candle list produced is fed into a **fresh** `SymbolIndicatorState()` (never the live singleton) bar-by-bar in chronological order, so indicator values are reconstructed exactly as they'd have looked at `T` — no shortcuts like loading the whole dataset and "promising not to look ahead."

## Evidence record

`validate_evidence()` (`app/research/evidence.py`) runs after data is loaded, before evaluation, and performs four checks:

| Check | What it actually verifies |
|---|---|
| `future_bar_check` | No candle across any symbol has `ts > as_of` (defense-in-depth — the fetch query already filters this, but the evidence layer re-verifies rather than trusting the caller) |
| `timestamp_order_check` | Each symbol's candle list is strictly chronological |
| `universe_check` | Every symbol with data is a member of the requested universe |
| `scan_version_check` | The scan has a non-empty stable hash (a presence check — there is no scan-catalog lookup to compare against, since no such catalog exists in this repo; documented honestly rather than implying more than it verifies) |

Overall status is `valid` only if all checks pass, `invalid` on any hard violation (future data, order violation), or `incomplete` if a symbol simply has no data (not a contradiction of the as-of cutoff, just missing).

## Fail-closed rule

If evidence is `invalid`, the run's final state is `FAILED` and `GET /api/research/runs/{run_id}/results` responds with `valid: false` and *"Historical replay unavailable: evidence validation failed."* The underlying data is still retained and returned alongside for diagnostics, but never presented as a trustworthy finding.

## Regression tests that prove this, not just assert it

- `test_research_replay_future_leakage.py`: builds two otherwise-identical candle fixtures for one symbol, one with a dramatic price spike at a timestamp just after `as_of`. The fake DB layer used in this test compiles the actual SQL `fetch_candle_history_as_of` generates and extracts the real bound `ts <= as_of` parameter before filtering rows — it does not trust the test to have pre-filtered anything. Replaying both fixtures at the same `as_of` produces byte-identical results, proving the spike was structurally invisible.
- `test_research_replay_determinism.py`: the same replay run twice produces identical `scan_hash`, signals, and evidence status.

## What this does not claim

Reproducibility requires code version + scan definition + data source + `as_of` + timezone all being recorded together (`RunManifest` carries all five). If the git SHA can't be resolved (e.g. `.git` unavailable in a container), `code_version` falls back to `"unknown"` rather than fabricating a value — reproducibility is then honestly incomplete, not silently assumed.
