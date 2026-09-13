# Architecture Audit — Phase 1

Conducted 2026-09-13 against the actual codebase (not the README, which overstates
several features — see `APP_OVERVIEW_FOR_CHATGPT.md` at the repo root for that
discrepancy list). This audit covers only the items the Phase 1 master prompt
flagged as suspect; it is not a full code review.

## Summary table

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Crossover semantics | ✅ Correct | Real prev-vs-current state check, not a bare inequality |
| 2 | Indicator key naming | ⚠️ Partial gap | `bollinger_mid` was never written — fixed this session |
| 3 | Candle persistence | ❌ Confirmed bug | One DB transaction per candle, unbatched |
| 4 | Volume semantics | ❌ Confirmed bug | Cumulative value double-counted as a delta — scoped to dead code |
| 5 | Pattern detection context | ❌ Confirmed gap | Only 2 candles ever supplied; 4 of 8 patterns can never fire |
| 6 | Blocking I/O in scan path | ✅ Not an issue | `screener_engine`/`condition_evaluator` are fully async, no I/O |
| 7 | `daily_setup.py` duplication | ❌ Confirmed | Two implementations existed; the unused one deleted this session |
| 8 | pandas-ta vs TA-Lib | ✅ Confirmed | pandas-ta is used throughout; no TA-Lib |
| 9 | Upstox V2 vs V3 | ❌ Confirmed | Streamer targets the V2 WebSocket URL |
| 10 | Dead deployment config | ❌ Confirmed | Railway/Render/Nixpacks files removed this session |
| 11 | Stale iOS/mobile URLs | ❌ Confirmed | iOS WebView hardcoded to dead Railway URL — fixed this session |

## Detail

### 1. Crossover semantics — correct

`apps/api/app/services/condition_evaluator.py` resolves both the current and
previous value of each operand and requires the relationship to have actually
changed:

```python
if op is ConditionOperator.CROSSES_ABOVE:
    return prev_left <= prev_right and left_val > right_val
return prev_left >= prev_right and left_val < right_val   # CROSSES_BELOW
```

This is a genuine crossover check. Limitation (not a bug): it only compares
bar *n-1* to bar *n* — there's no concept of "crossed within the last N bars."

### 2. Indicator key naming — `bollinger_mid` gap (fixed)

Redis key pattern `ind:{symbol}:{timeframe}` (via `redis_keys.indicator_key()`)
is used consistently by both writers (`indicator_engine.py`, `yahoo_finance.py`)
and the reader (`condition_evaluator.INDICATOR_NAMES`). One real gap: the reader
expects a `bollinger_mid` field, but `yahoo_finance.py`'s indicator-storage
mapping only ever wrote `bollinger_upper`/`bollinger_lower`. This was masked
in the live screener path because `screener_engine.py`'s enrichment step
synthesizes `bollinger_mid` from `sma_20` before evaluating conditions — but
any other consumer of the raw indicator hash would silently get `None`.
**Fixed this session**: `yahoo_finance.py` now extracts and stores the
`BBM_` column from `pandas_ta.bbands()` alongside upper/lower.

### 3. Candle persistence — one transaction per candle (unfixed, scoped to Phase 2)

`candle_builder.py`'s `_persist_1min` opens a new `SessionLocal()` and commits
a single row per completed candle, per symbol:

```python
async with SessionLocal() as session:
    session.add(row)
    await session.commit()
```

At NIFTY 500 scale with 1-minute candles this is ~500 individual transactions
per minute once the realtime engine is live. Not fixed now — it lives entirely
in the Upstox streamer code path, which is dead code today (see #9) and will
be rewritten from scratch in Phase 2 for the V3 protocol. Fixing the batching
now would be work Phase 2 immediately throws away.

### 4. Volume semantics — cumulative value treated as a delta (unfixed, scoped to Phase 2)

- The **live** data source, `nse_poller.py`, stores NSE's `totalTradedVolume`
  (cumulative day volume) as-is into `price:{symbol}` — correct, no delta math
  involved, no bug here.
- The **dead** V2 streamer path (`candle_builder.py`'s `_update`, fed by
  `upstox_streamer.py`) treats each incoming `volume` value as a **delta to
  add** to the running candle total. But Upstox's LTPC `vol` field is itself
  cumulative day volume, not a per-tick delta — so this path would overcount
  candle volume every tick, compounding across the session.
- Confirmed via `main.py`: only `nse_poller_loop` is started in the FastAPI
  lifespan; `UpstoxStreamer` is never imported there. This bug is real but
  currently inert. It must be fixed as part of the Phase 2 V3 rewrite (V3's
  `full` mode `ltpc.ltq`/`vtt` fields need to be read correctly — verify the
  exact field semantics against the current V3 proto before reimplementing).

### 5. Pattern detection — insufficient candle context (unfixed, scoped to Phase 2)

`pattern_detector.py` implements 8 candlestick patterns, 4 of which
(`morning_star`, `evening_star`, `three_white_soldiers`, `three_black_crows`)
require 3 candles. But `screener_engine.py`'s `_build_candle_list` only ever
supplies 2 (current + the `prev_*` fields already in the indicator hash) — so
those 4 patterns are dead code in the live screener today, even though the
detection logic for them exists and presumably works if given real 3-candle
input. This needs the realtime engine's proper bounded OHLCV history buffers
(Phase 2, §20 of the build spec) to supply real multi-candle context.

### 6. Blocking I/O — not an issue

`screener_engine.run_scan` and `condition_evaluator` are fully async with
Redis pipeline batch reads and pure in-memory Decimal/dict computation. No
synchronous DB/HTTP calls in the per-request scan-evaluation path.
`yahoo_finance.get_historical` is synchronous (`yf.download`) but is
documented in-file as needing `asyncio.to_thread()` and is a data-ingestion
function, not part of the scan hot path.

### 7. Duplicate `daily_setup.py` / dead `apps/api/data/` tree — removed this session

Two implementations existed:
- `apps/api/app/services/daily_setup.py` — the real one, wired for APScheduler
  (though not actually scheduled anywhere yet — worth wiring up in Phase 2).
- `apps/api/tasks/daily_setup.py` — an orphaned duplicate importing from a
  parallel `apps/api/data/` package (its own copies of `indicator_engine.py`,
  `candle_builder.py`, `upstox_streamer.py`, etc.), confirmed unreferenced by
  anything in `apps/api/app/` or any script/CI/docker-compose config.

**Deleted this session**: `apps/api/tasks/` and `apps/api/data/*.py` (the
`apps/api/data/nifty500_seed.json` file was kept — it's the live universe seed
`nse_poller.py` actually reads, despite living in the same directory as the
dead duplicate service files).

### 8. pandas-ta vs TA-Lib — confirmed

`requirements.txt` pins `pandas-ta>=0.4.67b0,<0.5.0b0`. Both
`indicator_engine.py` and `yahoo_finance.py` use it (`ta.rsi`, `ta.ema`,
`ta.macd`, `ta.bbands`, `ta.atr`, `ta.adx`, `ta.vwap`, `ta.sma`). No `talib`
import anywhere in the repo. TA-Lib migration (per the build spec, for its
150+ indicator library and BSD license) is a Phase 2/3 decision, not done yet.

### 9. Upstox V2 vs V3 — confirmed gap

`apps/api/app/services/upstox_streamer.py` connects to:

```python
_WS_URL = "wss://api.upstox.com/v2/feed/market-data-feed"
```

This is the **V2** endpoint. Verified against Upstox's current official docs
(fetched 2026-09-13): V3 uses a different authorization flow, binary Protobuf
messages (not V2's JSON/text format), `sub`/`unsub`/`change_mode` request
methods, and mode-based subscription limits (`ltpc` 5000, `full` 2000,
`option_greeks` 3000, `full_d30` 50 — Upstox Plus only). `upstox_auth.py` also
uses the standard OAuth2 authorization-code flow with **no refresh token
support** (`refresh_token()` raises unconditionally, forcing re-login) — the
Analytics Token (1-year validity, no OAuth redirect, read-only, generated
directly from the Developer Apps page) is a substantially better fit for this
project's single-owner, server-side-only usage pattern. See
`docs/DATA_PROVIDER_MATRIX.md`. Full V3 migration is Phase 2 scope.

### 10 & 11. Dead deployment config / stale URLs — fixed this session

Removed: `render.yaml`, `apps/web/railway.json`, `apps/api/railway.json`,
`apps/api/Procfile`, `apps/api/nixpacks.toml` — none were referenced by
anything; `apps/api/Dockerfile` is the sole build path.

Replaced `.github/workflows/deploy.yml` (previously ran `railway up` against
a dead `RAILWAY_TOKEN` on every push) with a CI-only workflow (backend
pytest, frontend lint/typecheck/build) — no deploy step, since Vercel deploys
via its own git integration and the Oracle Cloud deploy is a separate manual
SSH step for now.

Fixed `apps/ios/CodexScreener/ContentView.swift`, which hardcoded the dead
Railway URL as both the WebView's load URL and in its external-link
allowlist — now points at `https://breakoutscan-web.vercel.app`.

`apps/mobile` (Expo) was checked and has **no backend URL wired at all**,
stale or otherwise — it needs real configuration whenever that app is
actually built out further; not urgent for Phase 1.
