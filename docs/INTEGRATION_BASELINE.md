# Integration Baseline — Surgical AI + Research Integration

Recorded before any code in this integration was written, per the integration brief's §3.

- **Baseline commit**: `a152b3e` (Phase 3.4a: false-breakout guard, Breakout DNA scoring, Market Regime Engine)
- **Branch**: `feature/surgical-research-integrations` (created off `main` at `a152b3e`)
- **Baseline test command**: `cd apps/api && python -m pytest app/tests/ -q`
- **Baseline test result**: 232 passed, 0 failed
- **Python version**: 3.13.13 (local dev interpreter; container/production target is 3.12 per `apps/api/Dockerfile` and CI)
- **Node version**: v24.14.0 (local; CI pins Node 20 per `.github/workflows/deploy.yml`)
- **Dependency lock state**: no `pyproject.toml`/lock file exists — `apps/api/requirements.txt` + `requirements-dev.txt` are version-range pinned, not hash-locked. `apps/web/package.json` has no `engines` field.
- **Relevant existing AI paths**: `apps/api/app/services/ai_suggestions.py` (848 lines), routed via `apps/api/app/api/routes/ai_suggestions.py` (`GET /api/ai-suggestions`, `POST /api/ai-suggestions/refresh`, `GET /api/ai-suggestions/debug`). No Pydantic schema exists for its response today.
- **Relevant existing replay/backtest paths**: none. No `app/research/`, `app/backtest/`, or `app/replay/` package exists anywhere in the repo prior to this integration.
- **Live market engine is explicitly out of scope for this integration.** Nothing in `app/market/`, `app/breakouts/`, or `app/screener/` is being modified except one additive sibling function (`fetch_candle_history_as_of`) in `app/market/candles.py`, which the live pipeline never calls.
