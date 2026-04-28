<div align="center">

# BreakoutScan

### Real-time Indian market screener across API, web, and mobile surfaces

[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=fff)](#tech-stack)
[![Next.js](https://img.shields.io/badge/Next.js-Web_App-000?style=for-the-badge&logo=next.js)](#tech-stack)
[![Expo](https://img.shields.io/badge/Expo-Mobile_App-000020?style=for-the-badge&logo=expo)](#tech-stack)
[![Redis](https://img.shields.io/badge/Redis-Live_Pipeline-dc382d?style=for-the-badge&logo=redis&logoColor=fff)](#architecture-highlights)

</div>

---

## Recruiter Quick Scan

| Signal | Details |
|---|---|
| Product | Real-time NSE/BSE screener with backend services, web dashboard, and mobile app shell |
| What it demonstrates | Full-stack fintech architecture, live data streaming, scan engines, shared contracts, and deployment planning |
| Differentiator | Market-data pipeline designed around Redis caching, WebSockets, prebuilt scans, and alert workflows |
| Stack | FastAPI, Next.js, Expo, PostgreSQL/TimescaleDB, Redis, Docker, TypeScript, Python |

## Product Surface

- FastAPI backend for prices, indices, stocks, screeners, watchlists, alerts, and AI suggestions
- Next.js web app for dashboard, charts, fundamentals, screener views, alerts, and watchlists
- Expo mobile app foundation for iOS/Android market monitoring
- Shared contracts package for consistent API types across clients
- Docker Compose setup for local full-stack development

## Architecture Highlights

```text
apps/
  api/        FastAPI backend, database models, scan engine, services, WebSockets
  web/        Next.js frontend and market dashboard
  mobile/     Expo mobile application
packages/
  contracts/  Shared TypeScript contracts
```

Core backend modules:

- Upstox auth and streaming services
- NSE fallback and instrument loading
- Candle builder and indicator engine
- Prebuilt scans and custom condition evaluation
- Watchlist, alert, screener, and market routes

## Local Development

```bash
npm install
docker compose up --build
```

Open:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Web app: `http://localhost:3000`

## Scripts

```bash
npm run dev:web
npm run build:web
npm run test:api
npm run dev:mobile
```

## Tech Stack

| Layer | Tooling |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy, Alembic |
| Realtime | WebSockets, Redis, Upstox market data |
| Web | Next.js, React, TypeScript |
| Mobile | Expo, React Native |
| Data | PostgreSQL, TimescaleDB-ready migrations |
| Infra | Docker Compose, Railway config |
