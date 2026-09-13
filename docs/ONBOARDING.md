# Onboarding — Codex Screener (BreakoutScan)

## Prerequisites

- Node.js 20+, pnpm 9+
- Python 3.12, uv or pip
- Docker Desktop (for local Railway parity)
- Railway CLI (`npm i -g @railway/cli`)
- GitHub CLI (`gh`)

## Local Dev Setup

### 1. Clone and install

```bash
git clone <repo-url> "Codex Screener"
cd "Codex Screener"

# Frontend
cd apps/web && pnpm install

# Backend
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example apps/api/.env
# Fill in: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY,
#          GEMINI_API_KEY, GROQ_API_KEY
```

### 3. Run

```bash
# Terminal 1 — API
cd apps/api && uvicorn app.main:app --reload --port 8001

# Terminal 2 — Web
cd apps/web && pnpm dev
# → http://localhost:3000
```

### 4. Verify health

```bash
curl http://localhost:8001/health
# Expected: {"status":"ok","market":{"is_open":false,...},"poller_running":true}
```

## Deployment

### Railway API

```bash
railway login
railway link  # select BreakoutScan API project
railway up    # deploy from local
```

Or push to `main` — Railway auto-deploys on push.

### Frontend

Push to `main` — Vercel/Railway web auto-deploys.

## Common Tasks

### Add a new screener route

1. Create handler in `apps/api/app/api/routes/screener.py`
2. Apply `@limiter.limit(get_settings().rate_limit_screener)` decorator
3. Register in `apps/api/app/api/__init__.py` router include
4. Add frontend fetch in `apps/web/src/lib/api.ts`

### Change rate limits

Edit Railway env vars: `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_SCREENER`, `RATE_LIMIT_AI_REFRESH`.
Format: `"N/period"` where period = `second`, `minute`, `hour`, `day`.

### Update Python dependencies

```bash
# Test locally first
pip install -r requirements.txt
# Verify no OOM with: docker build -t test-api apps/api/
# Then update requirements.txt with specific pinned version
```

**Never** remove version pins without testing. See `docs/DECISIONS.md#dep-pinning`.

### Debug Railway build failure

```bash
railway logs --service api --lines 200
# Look for: "ERROR: Could not find a version" or "MemoryError"
```

## Key URLs

| Service | URL |
|---------|-----|
| Production API | `https://breakoutscan-api-production.up.railway.app` |
| Production Web | `https://breakoutscan-web-production.up.railway.app` |
| API Health | `https://breakoutscan-api-production.up.railway.app/health` |
| Supabase Dashboard | `https://supabase.com/dashboard` |
| Railway Dashboard | `https://railway.app/dashboard` |

## Project Structure

```
apps/api/app/
├── main.py           # FastAPI app, lifespan, poller watchdog
├── core/
│   ├── config.py     # All settings (pydantic-settings)
│   ├── rate_limit.py # slowapi limiter singleton
│   ├── logging.py    # Structured logging
│   └── errors.py     # Custom exception handlers
├── api/routes/       # Route handlers (screener, ai, health, auth)
├── services/         # Business logic (nse_poller, ai_service, etc.)
├── db/               # DB models + session
├── schemas/          # Pydantic request/response models
└── ws/               # WebSocket handlers
```
