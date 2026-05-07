# Architecture — Codex Screener (BreakoutScan)

## System Overview

```
User Browser
    │
    ▼
Next.js 15 (Vercel / Railway web)
    │  /api/* → rewrites to API
    │  WebSocket → WSS proxy
    ▼
FastAPI (Railway API service)
    ├── REST: /api/screener, /api/ai, /api/health
    ├── WebSocket: /ws (live market ticks)
    └── Background: NSE Poller (asyncio task, watchdog-wrapped)
         │
         ├── Supabase Postgres (primary DB — asyncpg / SQLAlchemy 2.0)
         │     Tables: stocks, indicators, universe, ohlcv, signals
         │
         ├── Redis / Upstash (cache layer)
         │     TTLs: indicators 600s, instruments 86400s, tokens 28800s
         │
         └── External APIs
               ├── NSE India (market data — unofficial)
               ├── Upstox SDK (broker data / OAuth)
               ├── Gemini API (AI analysis — primary)
               ├── Groq API (AI analysis — fallback #1)
               └── xAI Grok API (AI analysis — fallback #2)
```

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 15 |
| UI Components | shadcn/ui + Tailwind CSS | v4 |
| Backend | FastAPI | 0.111–0.135 |
| Python | 3.12 | — |
| ORM | SQLAlchemy async | 2.x |
| DB Driver | asyncpg | 0.29 |
| Database | Supabase (Postgres 15) | — |
| Cache | Redis (Upstash) | 5.x client |
| Data | pandas 2.x + pandas-ta 0.4.x + numpy 2.x | pinned |
| Rate Limiting | slowapi (starlette limiter) | 0.1.9 |
| Deployment | Railway (Docker) | — |

## AI Fallback Chain

```python
# Tier 1 — Gemini (fastest, cheapest)
# Tier 2 — Groq (fallback)
# Tier 3 — xAI Grok (last resort)
# On all failure → return cached result or empty analysis
```

Implemented in `apps/api/app/services/ai_service.py` (or equivalent).
Config keys: `GEMINI_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`.

## NSE Poller — Watchdog Pattern

```python
# main.py — _poller_watchdog()
# - Wraps nse_poller_loop() in try/except
# - Exponential back-off: 5s → 10s → 20s → ... capped at 300s
# - Logs crash reason; auto-restarts
# - _poller_running flag tracked for health endpoint
```

## Rate Limiting

All routes protected by `slowapi`. Limits are configurable via env:
- `RATE_LIMIT_DEFAULT` — general routes (default: `100/minute`)
- `RATE_LIMIT_SCREENER` — screener routes (default: `20/minute`)
- `RATE_LIMIT_AI_REFRESH` — AI routes (default: `5/minute`)

Exceeded → HTTP 429 (handled by `_rate_limit_exceeded_handler`).

## CORS Policy

Hardcoded allowed origins in `main.py`:
- `http://localhost:3000`
- `https://breakoutscan-web-production.up.railway.app`
- `https://breakoutscan.vercel.app` (if applicable)

Additional origins via `CORS_ALLOWED_ORIGINS` env var (comma-separated).

## Docker Build (Railway)

```dockerfile
# FROM python:3.12-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Critical**: `requirements.txt` must stay pinned. Unpinned pip install causes OOM during build on Railway's memory-constrained builders. The OOM was caused by pandas 3.x being pulled in when `pandas` was unpinned.

## Known Constraints

- **Railway memory**: ~512MB on Starter. Keep pandas 2.x (not 3.x) to stay within limits.
- **Supabase PgBouncer**: Use port `6543`, disable `statement_cache_size` in asyncpg (`prepared_statement_cache_size=0`).
- **No persistent filesystem**: Railway containers are ephemeral. All state must go to DB/Redis.
- **NSE data**: Unofficial NSE India scraping — subject to rate limits and IP blocks during peak hours.
