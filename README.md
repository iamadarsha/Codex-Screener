# BreakoutScan

BreakoutScan is a monorepo for a real-time NSE/BSE screener platform with:

- a FastAPI backend
- a Next.js 15 web app
- an Expo iOS app

## Local development

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open:
   - API: `http://localhost:8000/health`
   - Web: `http://localhost:3000`

## Repository layout

- `apps/api`: backend, migrations, data pipeline, screener engine
- `apps/web`: Next.js frontend
- `apps/mobile`: Expo mobile app
- `packages/contracts`: shared TypeScript contracts

