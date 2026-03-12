# BreakoutScan Implementation Plan

## Phase 0 Status

This repository is currently a greenfield workspace:

- No tracked source files exist yet.
- Git is initialized on `main`.
- No GitHub remote is configured yet.
- Local toolchain is available for the requested stack:
  - Docker 29.2.1
  - Docker Compose v5.1.0
  - Node.js v24.14.0
  - npm 11.9.0
  - Python 3.12.8

This plan assumes we will start locally, commit phase-by-phase in git, and leave GitHub remote setup as an external prerequisite unless credentials and a target repo are provided later.

## Delivery Strategy

We will build BreakoutScan as a monorepo with three applications and one shared contracts package:

- `apps/api`: FastAPI backend, data pipeline, screener engine, Celery worker, Alembic migrations
- `apps/web`: Next.js 15 web frontend with the requested E8-style trading terminal design system
- `apps/mobile`: Expo SDK 51 iOS app using Expo Router and Reanimated 3
- `packages/contracts`: shared TypeScript contracts for frontend/mobile API typing

We will execute the user-requested phases in order and commit only after the phase-specific verification passes.

## Planned Repository Layout

```text
.
├── .dockerignore
├── .editorconfig
├── .env.example
├── .gitignore
├── IMPLEMENTATION_PLAN.md
├── README.md
├── docker-compose.yml
├── package.json
├── package-lock.json
├── tsconfig.base.json
├── apps
│   ├── api
│   │   ├── Dockerfile
│   │   ├── alembic.ini
│   │   ├── requirements.txt
│   │   ├── scripts
│   │   │   ├── healthcheck.py
│   │   │   ├── seed_stocks.py
│   │   │   ├── backfill_ohlcv.py
│   │   │   ├── run_pipeline_smoke.py
│   │   │   └── benchmark_screener.py
│   │   ├── alembic
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions
│   │   │       ├── 0001_enable_timescaledb_and_core_tables.py
│   │   │       ├── 0002_create_ohlcv_hypertables.py
│   │   │       ├── 0003_create_user_watchlist_alert_scan_tables.py
│   │   │       └── 0004_add_indexes_and_constraints.py
│   │   ├── app
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── errors.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── logging.py
│   │   │   │   └── security.py
│   │   │   ├── db
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── session.py
│   │   │   │   ├── enums.py
│   │   │   │   └── models
│   │   │   │       ├── __init__.py
│   │   │   │       ├── stock.py
│   │   │   │       ├── ohlcv.py
│   │   │   │       ├── user_scan.py
│   │   │   │       ├── scan_run.py
│   │   │   │       ├── watchlist.py
│   │   │   │       ├── alert.py
│   │   │   │       └── alert_history.py
│   │   │   ├── schemas
│   │   │   │   ├── __init__.py
│   │   │   │   ├── common.py
│   │   │   │   ├── stock.py
│   │   │   │   ├── fundamentals.py
│   │   │   │   ├── screener.py
│   │   │   │   ├── watchlist.py
│   │   │   │   ├── alert.py
│   │   │   │   ├── market.py
│   │   │   │   ├── auth.py
│   │   │   │   └── websocket.py
│   │   │   ├── api
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deps.py
│   │   │   │   └── routes
│   │   │   │       ├── __init__.py
│   │   │   │       ├── auth.py
│   │   │   │       ├── stocks.py
│   │   │   │       ├── screener.py
│   │   │   │       ├── indices.py
│   │   │   │       ├── prices.py
│   │   │   │       ├── market.py
│   │   │   │       ├── watchlist.py
│   │   │   │       ├── alerts.py
│   │   │   │       └── fundamentals.py
│   │   │   ├── services
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── stock_service.py
│   │   │   │   ├── watchlist_service.py
│   │   │   │   ├── alert_service.py
│   │   │   │   ├── fundamentals_service.py
│   │   │   │   ├── market_service.py
│   │   │   │   ├── live_price_service.py
│   │   │   │   ├── upstox_auth.py
│   │   │   │   ├── upstox_instruments.py
│   │   │   │   ├── upstox_streamer.py
│   │   │   │   ├── nse_fallback.py
│   │   │   │   ├── history_backfill.py
│   │   │   │   ├── candle_builder.py
│   │   │   │   ├── indicator_engine.py
│   │   │   │   ├── screener_engine.py
│   │   │   │   ├── condition_evaluator.py
│   │   │   │   ├── prebuilt_scans.py
│   │   │   │   ├── pattern_detector.py
│   │   │   │   ├── orb.py
│   │   │   │   ├── redis_cache.py
│   │   │   │   ├── websocket_broadcast.py
│   │   │   │   └── supabase_client.py
│   │   │   ├── tasks
│   │   │   │   ├── __init__.py
│   │   │   │   ├── celery_app.py
│   │   │   │   ├── schedules.py
│   │   │   │   ├── market_open.py
│   │   │   │   ├── instrument_sync.py
│   │   │   │   ├── token_refresh.py
│   │   │   │   ├── alert_dispatch.py
│   │   │   │   └── indicator_refresh.py
│   │   │   ├── ws
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py
│   │   │   │   ├── prices.py
│   │   │   │   ├── scans.py
│   │   │   │   └── alerts.py
│   │   │   ├── utils
│   │   │   │   ├── __init__.py
│   │   │   │   ├── decimals.py
│   │   │   │   ├── time.py
│   │   │   │   ├── retry.py
│   │   │   │   ├── redis_keys.py
│   │   │   │   └── indicators.py
│   │   │   └── tests
│   │   │       ├── __init__.py
│   │   │       ├── conftest.py
│   │   │       ├── test_health.py
│   │   │       ├── test_models.py
│   │   │       ├── test_migrations.py
│   │   │       ├── test_upstox_auth.py
│   │   │       ├── test_nse_fallback.py
│   │   │       ├── test_indicator_engine.py
│   │   │       ├── test_condition_evaluator.py
│   │   │       ├── test_prebuilt_scans.py
│   │   │       ├── test_screener_engine.py
│   │   │       ├── test_api_stocks.py
│   │   │       ├── test_api_screener.py
│   │   │       ├── test_api_watchlist.py
│   │   │       ├── test_api_alerts.py
│   │   │       └── test_websockets.py
│   ├── web
│   │   ├── Dockerfile
│   │   ├── next-env.d.ts
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   ├── postcss.config.js
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── public
│   │   │   ├── icons
│   │   │   │   └── logo-mark.svg
│   │   │   └── images
│   │   │       └── hero-grid.svg
│   │   └── src
│   │       ├── app
│   │       │   ├── globals.css
│   │       │   ├── layout.tsx
│   │       │   ├── page.tsx
│   │       │   ├── dashboard/page.tsx
│   │       │   ├── screener/page.tsx
│   │       │   ├── chart/[symbol]/page.tsx
│   │       │   ├── watchlist/page.tsx
│   │       │   ├── fundamentals/page.tsx
│   │       │   ├── alerts/page.tsx
│   │       │   ├── loading.tsx
│   │       │   ├── error.tsx
│   │       │   └── not-found.tsx
│   │       ├── components
│   │       │   ├── layout
│   │       │   │   ├── app-shell.tsx
│   │       │   │   ├── sidebar.tsx
│   │       │   │   ├── topbar.tsx
│   │       │   │   └── page-transition.tsx
│   │       │   ├── ui
│   │       │   │   ├── card.tsx
│   │       │   │   ├── button.tsx
│   │       │   │   ├── badge.tsx
│   │       │   │   ├── input.tsx
│   │       │   │   ├── modal.tsx
│   │       │   │   ├── skeleton.tsx
│   │       │   │   ├── live-dot.tsx
│   │       │   │   ├── animated-number.tsx
│   │       │   │   ├── price-cell.tsx
│   │       │   │   ├── countdown-bar.tsx
│   │       │   │   ├── section-heading.tsx
│   │       │   │   └── data-table.tsx
│   │       │   ├── landing
│   │       │   │   ├── hero.tsx
│   │       │   │   ├── particle-mesh.tsx
│   │       │   │   ├── live-mock-table.tsx
│   │       │   │   ├── feature-grid.tsx
│   │       │   │   └── comparison-table.tsx
│   │       │   ├── dashboard
│   │       │   │   ├── stat-cards.tsx
│   │       │   │   ├── breakout-feed.tsx
│   │       │   │   ├── breadth-donut.tsx
│   │       │   │   ├── volume-surges.tsx
│   │       │   │   ├── sector-heatmap.tsx
│   │       │   │   └── active-scan-toggles.tsx
│   │       │   ├── screener
│   │       │   │   ├── prebuilt-scan-grid.tsx
│   │       │   │   ├── scan-results-panel.tsx
│   │       │   │   ├── custom-scan-builder.tsx
│   │       │   │   ├── condition-row.tsx
│   │       │   │   ├── logic-preview.tsx
│   │       │   │   └── sortable-results-table.tsx
│   │       │   ├── chart
│   │       │   │   ├── price-chart.tsx
│   │       │   │   ├── timeframe-tabs.tsx
│   │       │   │   ├── indicator-pills.tsx
│   │       │   │   ├── stock-snapshot.tsx
│   │       │   │   ├── signals-card.tsx
│   │       │   │   ├── volume-panel.tsx
│   │       │   │   ├── rsi-panel.tsx
│   │       │   │   └── macd-panel.tsx
│   │       │   ├── watchlist
│   │       │   │   ├── watchlist-table.tsx
│   │       │   │   ├── add-stock-modal.tsx
│   │       │   │   ├── watchlist-summary.tsx
│   │       │   │   └── ema-status-badge.tsx
│   │       │   ├── fundamentals
│   │       │   │   ├── filter-sidebar.tsx
│   │       │   │   ├── range-slider.tsx
│   │       │   │   ├── results-table.tsx
│   │       │   │   └── radar-panel.tsx
│   │       │   └── alerts
│   │       │       ├── alert-form.tsx
│   │       │       ├── active-alerts-list.tsx
│   │       │       └── history-timeline.tsx
│   │       ├── hooks
│   │       │   ├── use-live-prices.ts
│   │       │   ├── use-scan-run.ts
│   │       │   ├── use-market-breadth.ts
│   │       │   ├── use-watchlist.ts
│   │       │   └── use-alerts.ts
│   │       ├── lib
│   │       │   ├── api.ts
│   │       │   ├── api-types.ts
│   │       │   ├── chart-colors.ts
│   │       │   ├── constants.ts
│   │       │   ├── query-client.ts
│   │       │   ├── socket.ts
│   │       │   ├── format.ts
│   │       │   ├── cn.ts
│   │       │   └── mock-data.ts
│   │       ├── store
│   │       │   └── live-price-store.ts
│   │       └── types
│   │           └── chart.ts
│   └── mobile
│       ├── app.json
│       ├── babel.config.js
│       ├── eas.json
│       ├── metro.config.js
│       ├── package.json
│       ├── tsconfig.json
│       ├── app
│       │   ├── _layout.tsx
│       │   ├── modal.tsx
│       │   ├── chart/[symbol].tsx
│       │   ├── scan/[id].tsx
│       │   └── (tabs)
│       │       ├── _layout.tsx
│       │       ├── index.tsx
│       │       ├── scan.tsx
│       │       ├── watchlist.tsx
│       │       └── alerts.tsx
│       └── src
│           ├── components
│           │   ├── layout
│           │   │   ├── screen.tsx
│           │   │   └── app-header.tsx
│           │   ├── home
│           │   │   ├── market-status.tsx
│           │   │   ├── index-ticker-list.tsx
│           │   │   ├── breakout-feed-list.tsx
│           │   │   └── breadth-donut.tsx
│           │   ├── scan
│           │   │   ├── scan-section-list.tsx
│           │   │   ├── scan-results-list.tsx
│           │   │   └── loading-lottie.tsx
│           │   ├── chart
│           │   │   ├── candle-chart.tsx
│           │   │   ├── crosshair-overlay.tsx
│           │   │   ├── indicator-sheet.tsx
│           │   │   └── live-price-chip.tsx
│           │   ├── watchlist
│           │   │   ├── draggable-watchlist.tsx
│           │   │   ├── add-stock-sheet.tsx
│           │   │   └── watchlist-row.tsx
│           │   └── alerts
│           │       ├── push-permission-gate.tsx
│           │       ├── alert-toggle-list.tsx
│           │       └── alert-history-timeline.tsx
│           ├── lib
│           │   ├── api.ts
│           │   ├── socket.ts
│           │   ├── haptics.ts
│           │   ├── notifications.ts
│           │   └── constants.ts
│           ├── store
│           │   ├── live-price-store.ts
│           │   ├── watchlist-store.ts
│           │   └── alert-store.ts
│           ├── theme
│           │   ├── colors.ts
│           │   ├── spacing.ts
│           │   ├── typography.ts
│           │   └── shadows.ts
│           ├── types
│           │   └── navigation.ts
│           └── animations
│               ├── fade-in-down.ts
│               ├── price-flash.ts
│               └── swipe-actions.ts
├── packages
│   └── contracts
│       ├── package.json
│       ├── tsconfig.json
│       └── src
│           ├── index.ts
│           ├── api.ts
│           ├── screener.ts
│           ├── market.ts
│           ├── watchlist.ts
│           └── alerts.ts
└── infra
    ├── cloudrun
    │   ├── api-service.yaml
    │   └── worker-service.yaml
    ├── github
    │   └── workflows
    │       ├── ci.yml
    │       ├── deploy-api.yml
    │       ├── deploy-web.yml
    │       └── ios-build.yml
    ├── scheduler
    │   └── jobs.md
    └── vercel
        └── project.json
```

## Dependency Plan

### Root Workspace

- `typescript`
- `eslint`
- `prettier`
- `@types/node`
- `npm` workspaces only, no secondary package manager

### Web App Dependencies

- `next`
- `react`
- `react-dom`
- `typescript`
- `tailwindcss`
- `postcss`
- `autoprefixer`
- `framer-motion`
- `lightweight-charts`
- `recharts`
- `zustand`
- `@tanstack/react-query`
- `@tanstack/react-table`
- `@dnd-kit/core`
- `@dnd-kit/sortable`
- `@dnd-kit/utilities`
- `react-hook-form`
- `@hookform/resolvers`
- `zod`
- `sonner`
- `lucide-react`
- `clsx`
- `tailwind-merge`
- `@supabase/supabase-js`

### Mobile App Dependencies

- `expo`
- `expo-router`
- `react`
- `react-native`
- `react-native-reanimated`
- `react-native-gesture-handler`
- `react-native-screens`
- `react-native-safe-area-context`
- `react-native-svg`
- `react-native-draggable-flatlist`
- `lottie-react-native`
- `expo-notifications`
- `expo-haptics`
- `@gorhom/bottom-sheet`
- `zustand`
- `@tanstack/react-query`
- `@shopify/react-native-skia`
- `victory-native`

### Backend Dependencies

- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy`
- `asyncpg`
- `alembic`
- `pydantic`
- `pydantic-settings`
- `redis`
- `httpx`
- `python-socketio`
- `celery`
- `apscheduler`
- `pandas`
- `pandas-ta`
- `yfinance`
- `upstox-python-sdk`
- `protobuf`
- `orjson`
- `python-dotenv`
- `supabase`
- `tenacity`
- `structlog`
- `pytest`
- `pytest-asyncio`
- `pytest-cov`
- `respx`

### Infrastructure Dependencies

- PostgreSQL 16 with TimescaleDB extension
- Redis 7
- Cloud Run runtime for API and worker
- Vercel for web hosting
- Cloud Scheduler for 08:00 / 08:45 / 09:00 IST jobs
- Expo EAS Build for iOS distribution
- GitHub Actions for CI/CD

## Integration Points

### Market Data

- Upstox OAuth2 login and callback flow
- Upstox instrument CSV download at 08:00 IST
- Upstox WebSocket V3 market feed with protobuf decoding
- NSE API fallback for indices and single-symbol quote data
- yfinance for historical OHLCV backfill only

### Storage and Messaging

- PostgreSQL 16 for canonical relational data
- TimescaleDB hypertables for OHLCV storage
- Redis for:
  - token storage with TTL
  - symbol and instrument maps with TTL
  - live prices with TTL
  - pub/sub tick fan-out
  - indicator hashes with TTL
  - screener hot caches with TTL

### User Data and Auth

- Supabase for web/mobile auth state, watchlists, alerts, and user metadata
- Backend service-role client for protected mutations and synchronization

### Frontend Runtime

- FastAPI REST endpoints for data fetches
- FastAPI WebSocket endpoints for live prices, scans, and alerts
- TanStack Query for caching and invalidation
- Zustand stores for real-time price state

### Mobile Runtime

- Expo Notifications for push alerts
- Expo Haptics for press and swipe feedback
- Reanimated 3 worklets for all runtime animations

### Deployments

- Cloud Run service for API
- Cloud Run service for Celery worker or scheduled background worker
- Vercel project for web
- Cloud Scheduler for daily and market-open workflows
- EAS Build pipeline for iOS

## Implementation Details by Phase

## Phase 1: Scaffold

### Goals

- Create the full monorepo structure
- Add root workspace configuration
- Add `docker-compose.yml`
- Add `Dockerfile`s for API and web
- Add backend `requirements.txt`
- Add Alembic bootstrap files
- Add `.env.example`
- Make `docker compose up` produce four healthy services:
  - `postgres`
  - `redis`
  - `api`
  - `web`

### Verification

- `docker compose up --build -d`
- `docker compose ps`
- API health endpoint returns success
- Web health route returns success
- Postgres healthcheck passes
- Redis healthcheck passes

### Planned Commit

- `phase 1: scaffold monorepo, compose stack, and app skeletons`

## Phase 2: Database

### Goals

- Implement SQLAlchemy models
- Implement Alembic migrations
- Enable TimescaleDB extension
- Create the required hypertable and indexes
- Seed `stocks` with NIFTY500 data and static fundamental seed columns
- Verify 10k OHLCV insert/query behavior

### Verification

- `alembic upgrade head`
- hypertable exists
- insert 10k `ohlcv_1min` rows
- query latest rows by `(symbol, ts desc)` index
- seed script populates stock metadata

### Planned Commit

- `phase 2: add database schema, migrations, and stock seed data`

## Phase 3: Data Pipeline

### Goals

- Implement Upstox OAuth2 token exchange and refresh
- Implement instrument CSV ingestion
- Build Redis symbol maps with TTL
- Implement WebSocket streamer with protobuf decoding
- Build candle aggregation buffers
- Compute indicators with pandas-ta
- Add NSE fallback switching after 60 seconds of tick silence

### Verification

- OAuth2 redirect and callback smoke-tested locally
- instrument maps present in Redis
- live ticks ingested for subscribed instruments
- 1min, 5min, 15min candle formation validated
- indicator values match controlled calculations
- 10-minute smoke run produces populated `ind:{symbol}:{tf}` hashes

### Planned Commit

- `phase 3: implement live market data pipeline`

## Phase 4: Screener Engine

### Goals

- Implement the 14 operators
- Implement lookback handling and compare-indicator semantics
- Implement ORB logic and candlestick pattern detection
- Encode all 12 prebuilt scans
- Optimize `evaluate_scan` for sub-1.5s execution on 2000 symbols

### Verification

- unit tests for each operator
- correctness tests for patterns and ORB
- prebuilt scan definition coverage tests
- 2000-symbol benchmark under 1.5 seconds

### Planned Commit

- `phase 4: add screener engine and prebuilt scan library`

## Phase 5: Backend API

### Goals

- Add all REST endpoints
- Add all WebSocket endpoints
- Add request/response schemas
- Add WebSocket manager and broadcast hooks
- Add Celery tasks and scheduler bindings

### Verification

- route tests pass
- manual `/docs` verification
- `wscat` verification for prices, scans, and alerts sockets

### Planned Commit

- `backend complete — all endpoints verified`

## Phase 6: Web Frontend

### Goals

- Implement the E8-style design system tokens globally
- Build persistent sidebar and topbar
- Build all seven pages in the required order
- Implement all requested animations
- Connect to live backend APIs and sockets

### Verification

- page routing works
- live prices stream into the UI
- screener runs against backend
- chart page renders and updates live
- watchlist/alerts/fundamentals flows work end to end

### Planned Commit

- `web frontend complete`

## Phase 7: iOS App

### Goals

- Scaffold Expo Router app
- Implement E8 theme tokens in React Native
- Implement 5 tabs and required secondary screens
- Ensure all motion is on Reanimated worklets
- Wire API, sockets, notifications, gestures, and haptics

### Verification

- iOS simulator boot succeeds
- tab navigation works
- gestures and bottom sheets work
- live prices stream into chart and lists
- animations remain smooth and JS-thread-free for motion

### Planned Commit

- `iOS app complete`

## Phase 8: Deploy

### Goals

- Add CI workflows
- Add Cloud Run manifests and deploy scripts
- Add Vercel config
- Add EAS config
- Document Cloud Scheduler jobs

### Verification

- API deploys to Cloud Run
- web deploys to Vercel
- scheduler jobs configured for daily instrument/token flows
- iOS build configuration valid for TestFlight submission

### Planned Commit

- `deployed to production`

## Design System Translation Plan

The user requested exact use of the E8-inspired visual language. We will encode the provided tokens directly into:

- web CSS custom properties in `apps/web/src/app/globals.css`
- Tailwind theme extensions in `apps/web/tailwind.config.ts`
- mobile color constants in `apps/mobile/src/theme/colors.ts`
- chart palettes in both web and mobile chart helpers

The required animation set will be implemented as follows:

- price flash: CSS keyframes on the web, Reanimated color timing on mobile
- number ticker: `requestAnimationFrame` interpolation on the web, Reanimated shared values on mobile
- scan results stagger: Framer Motion on the web, Reanimated entering animations on mobile
- scan toast: Sonner custom toast renderer on the web, in-app animated banner on mobile
- skeleton shimmer: CSS gradient animation on the web, Reanimated linear gradient shimmer on mobile
- page transitions: `AnimatePresence` on the web, Expo Router layout transitions on mobile where appropriate
- market pulse: reusable live-indicator component on both platforms
- modal: Framer Motion on the web, Reanimated scale and opacity animation on mobile

## Data Model Plan

### Database Tables

- `stocks`
- `ohlcv_1min`
- `ohlcv_daily`
- `user_scans`
- `scan_runs`
- `watchlist`
- `alerts`
- `alert_history`

### Redis Key Strategy

Every key will be written with expiration to satisfy the non-negotiable TTL rule:

- `upstox:token`
- `upstox:oauth_state:{nonce}`
- `instrument:symbol_to_key`
- `instrument:key_to_symbol`
- `universe:nifty50`
- `universe:nifty500`
- `ltp:{instrument_key}`
- `ltp:symbol:{symbol}`
- `ind:{symbol}:{tf}`
- `scan:last_run:{scan_hash}`
- `fallback:nse:last_success`
- `ws:last_tick_at`

## Non-Negotiable Rule Enforcement

- TypeScript strict mode will be enabled in all TS projects
- No `any` types will be introduced
- money values will use Python `Decimal`, SQL `NUMERIC`, and string-safe transport to clients
- env vars will be documented only in root `.env.example`
- all async functions in backend services will wrap external I/O with typed `try/except`
- WebSocket reconnect logic will use exponential backoff capped at 30 seconds
- price flash effects will avoid layout-triggering properties
- the screener benchmark will be part of automated verification

## Risks and Mitigations

### 1. Scope Risk

This is a very large greenfield build spanning backend, web, mobile, data infra, and deploy pipelines. We will reduce delivery risk by honoring the explicit phase boundaries and keeping each phase independently runnable.

### 2. External Credential Risk

Upstox, Supabase, Cloud Run, Vercel, and Expo EAS all require credentials that are not present yet. We can scaffold and validate local behavior with mocks or health routes, but full end-to-end live verification will require valid credentials.

### 3. GitHub Remote Missing

There is no configured remote repository. We can commit locally after each passing phase, but cannot satisfy remote push or GitHub Actions execution until a remote is attached.

### 4. NSE Access Stability

NSE API endpoints are known to be sensitive to cookie/session handling and anti-bot protections. We will isolate fallback logic behind a resilient HTTP client with retriable session bootstrap and clear circuit-breaker behavior.

### 5. Upstox Feed Capacity and Market Hours

Live feed verification depends on market state and valid instrument subscriptions. We will implement replayable smoke scripts and unit coverage so progress does not block entirely on market hours.

### 6. Mobile Monorepo Complexity

Expo + npm workspaces can require careful Metro configuration. We will keep shared packages minimal and verify simulator boot early in the mobile phase.

### 7. Design Fidelity Risk

The requested aesthetic is highly specific. We will encode the design tokens first, then build reusable primitives so later pages stay visually consistent instead of page-by-page drifting.

## Immediate Execution Plan

After this document is created, execution begins with Phase 1:

1. Create the root workspace, app directories, and base configs.
2. Build minimal API and web health endpoints.
3. Add Docker and Compose wiring for Postgres, Redis, API, and web.
4. Bring the stack up and verify all health checks.
5. Commit the passing Phase 1 scaffold locally.
