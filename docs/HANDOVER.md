# GitAgent Handover — Codex Screener (BreakoutScan)

**Date:** 2026-03-24
**Branch:** main
**Status:** Production live — API recovering after dependency-OOM fix

---

## What Just Happened (Last 3 Sessions)

| Commit | Change | Why |
|--------|--------|-----|
| `8d4d024` | Rate limiting (slowapi), CORS hardening, debug endpoint guard | Security hardening sprint |
| `150b237` | First attempt at pinning requirements.txt | Prevent OOM on Railway cold start |
| `68ce18e` | Pinned `pandas-ta==0.3.14b0` | **BROKEN** — version doesn't exist on PyPI |
| `be6e4bd` | Fixed: `numpy>=2.2.6,<3.0.0`, `pandas>=2.2.0,<3.0.0`, `pandas-ta>=0.4.67b0,<0.5.0b0` | Resolves Railway build error |
| `0a622c7` | Multi-layer failsafe platform hardening | Reliability sprint — poller watchdog, circuit breaker, graceful degradation |

## Current Blockers

- **Railway**: Verify latest build (`be6e4bd` or later) succeeded. Check Railway dashboard logs.
- **`ENVIRONMENT=production`** must be set in Railway environment variables dashboard (not yet confirmed).
- **Supabase RLS**: Row-level security policies not yet reviewed — users can currently read all rows.

## Immediate Next Steps for a New Agent

1. `gh run list --limit 5` — confirm Railway deploy is green after `be6e4bd`.
2. Verify `https://breakoutscan-api-production.up.railway.app/health` returns `200`.
3. Set `ENVIRONMENT=production` in Railway dashboard if not set.
4. Review Supabase RLS policies for `stocks`, `indicators`, `universe` tables.
5. Merge worktree branch `feature/security-hardening` or delete it (it's stale — main is ahead).

---

## File Map (Key Files Only)

```
Codex Screener/
├── apps/
│   ├── api/                          FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py               Entry point, lifespan, poller watchdog
│   │   │   ├── core/
│   │   │   │   ├── config.py         Pydantic-settings (all env vars)
│   │   │   │   ├── rate_limit.py     slowapi Limiter singleton
│   │   │   │   └── logging.py        Structured logging setup
│   │   │   ├── api/routes/
│   │   │   │   ├── screener.py       /api/screener/* — rate limited
│   │   │   │   └── ai_suggestions.py /api/ai/* — rate limited (5/min)
│   │   │   └── services/
│   │   │       └── nse_poller.py     Market data polling (watchdog-wrapped)
│   │   ├── requirements.txt          PINNED — do not loosen without testing
│   │   └── Dockerfile                python:3.12-slim, uvicorn
│   └── web/                          Next.js 15 frontend
│       └── src/
│           ├── components/layout/
│           │   ├── topbar.tsx        isOpen = status?.is_open ?? false
│           │   └── sidebar.tsx       Same null-safe pattern
│           └── app/dashboard/        Main dashboard page
├── docs/                             Agent handover package (this folder)
└── .env.example                      All required env var names
```

---

## Environment Variables Checklist

| Variable | Where | Status |
|----------|-------|--------|
| `DATABASE_URL` | Railway | ✅ Set |
| `SUPABASE_URL` | Railway | ✅ Set |
| `SUPABASE_SERVICE_KEY` | Railway | ✅ Set |
| `GEMINI_API_KEY` | Railway | ✅ Set |
| `GROQ_API_KEY` | Railway | ✅ Set |
| `ENVIRONMENT` | Railway | ⚠️ Needs `production` |
| `CORS_ALLOWED_ORIGINS` | Railway | ⚠️ Should include prod frontend URL |
| `RATE_LIMIT_DEFAULT` | Railway | Optional (default: `100/minute`) |
