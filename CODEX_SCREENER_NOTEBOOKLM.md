# Codex Screener: Complete Project Knowledge Base

## Project Overview

Codex Screener (internal codename: BreakoutScan) is a real-time Indian stock market screener platform built for NSE (National Stock Exchange) and BSE (Bombay Stock Exchange) stocks. It targets Indian retail traders and investors who want real-time technical analysis without paying for expensive platforms. The platform is live at screenercodex.netlify.app with a backend API at breakoutscan-api-production.up.railway.app. It is built as a monorepo containing a FastAPI Python backend, a Next.js 15 web frontend, and a native iOS app.

---

## Frontend Tech Stack

The frontend is a Next.js 15.3.1 web application using the App Router pattern with React 19.1.0 and TypeScript 5.8.3 for type safety.

### Core Framework
- Next.js 15.3.1: React framework with App Router for server-side rendering and static generation
- React 19.1.0: UI component library
- TypeScript 5.8.3: Static type checking across the entire frontend

### Styling and Design
- Tailwind CSS 3.4.17: Utility-first CSS framework for rapid styling
- Dark Terminal Theme: Custom dark color scheme inspired by trading terminals, using zinc/slate backgrounds with emerald/red accent colors for up/down movements
- Framer Motion 12.10.5: Animation library for page transitions, card reveals, and micro-interactions
- clsx 2.1.1 and tailwind-merge 3.2.0: Class name utilities for conditional styling

### State Management
- Zustand 5.0.3: Lightweight client-side state management for live price data and WebSocket state
- React Query (TanStack Query) 5.75.4: Server state management with automatic caching, refetching, and background updates for all API calls

### Data Visualization
- TradingView Lightweight Charts 5.0.8: Professional-grade candlestick charts with volume panels, used for the Charts page
- Recharts 2.15.3: React charting library for donut charts (market breadth) and bar charts (volume)

### UI Components and Utilities
- Lucide React 0.503.0: Icon library with 1500+ SVG icons
- React Hook Form 7.56.3: Performant form handling with minimal re-renders
- Zod 3.24.4: Schema validation library paired with React Hook Form
- TanStack React Table 8.21.3: Headless table library for sortable, filterable data tables
- Sonner 2.0.3: Toast notification system

### Deployment
- Netlify: Auto-deploys from GitHub main branch, serves the Next.js SSR application

---

## Backend Tech Stack

The backend is a FastAPI application written in Python 3.11+ deployed on Railway.

### Core Framework
- FastAPI: Modern async Python web framework with automatic OpenAPI docs
- Uvicorn: ASGI server running the FastAPI application
- Pydantic Settings: Configuration management loading from environment variables

### Database and ORM
- PostgreSQL 16 with TimescaleDB: Primary database hosted on Supabase (region: ap-south-1), using TimescaleDB hypertables for time-series OHLCV data
- SQLAlchemy 2.0+ (async): Object-relational mapper with async session support
- Alembic: Database migration tool with 4 migration versions tracking schema evolution

### Caching
- Redis 7: In-memory cache hosted on Railway (Upstash-compatible), storing 461 price keys, 380 indicator keys, AI suggestion cache, market indices, and scan results
- Redis key patterns: price:{SYMBOL} for JSON price data (300s TTL), ind:{SYMBOL}:1d for indicator hashes (600s TTL), ai:suggestions cached until 9 AM next trading day, market:indices and market:breadth for market overview

### HTTP and Networking
- httpx: Async HTTP client for external API calls
- feedparser: RSS feed parser for news aggregation across 10 sources
- yfinance: Yahoo Finance Python library for historical OHLCV data and indicator computation

### AI and Machine Learning
- Google Generative AI (google-generativeai): Gemini 2.0 Flash model for primary AI stock suggestions
- Groq SDK: Llama 3.3 70B model as secondary AI fallback
- xAI SDK: Grok model as tertiary AI option

### Logging and Monitoring
- structlog: Structured logging with JSON output for production debugging

### Deployment
- Railway: Auto-deploys backend from GitHub main branch with Docker support
- Docker and Docker Compose: Local development environment with PostgreSQL, Redis, API, and web containers
- Nixpacks: Build system used by Railway for automated builds

---

## iOS App Tech Stack

- SwiftUI: Apple's declarative UI framework for the app shell
- WKWebView: WebKit view loading the production Netlify URL
- Swift 5.9+: Programming language
- Xcode 26.3: Build tool and IDE
- Bundle ID: com.codexscreener.app
- Apple Developer Team ID: UW23XR9FK2
- Features: Purple gradient launch screen with "BS" logo, pull-to-refresh, external link handling in Safari

---

## External Services and APIs

### Stock Market Data Sources
1. NSE via indianapi.in: Primary source for real-time NSE stock listings, trending stocks, IPO data, and mutual fund information. Authenticated via API key in request headers.
2. Yahoo Finance (yfinance library): Historical OHLCV (Open, High, Low, Close, Volume) data for all timeframes. Computes technical indicators including RSI, EMA, MACD, and Bollinger Bands. No authentication required.
3. Upstox API v2: Real-time tick data via WebSocket for live price updates. Uses OAuth2 authentication with client ID and secret.
4. NSE Direct (nse-fallback): Fallback market data source using direct web scraping for index values and market status when primary sources fail.

### AI and Large Language Model Services
1. Google Gemini 2.0 Flash (Layer 1): Primary AI engine for generating stock suggestions. Uses two API keys (primary and backup) for redundancy. Each key has daily free-tier quota limits. Integrated via google-generativeai Python SDK.
2. Groq with Llama 3.3 70B (Layer 2): Secondary AI fallback when Gemini quota is exhausted. Free tier provides approximately 500,000 tokens per day. No credit card required. OpenAI-compatible API.
3. xAI Grok (Layer 2 alternate): Additional AI fallback integrated alongside Groq for redundancy.
4. Technical Scoring Engine (Layer 3): Zero-API-dependency fallback that uses RSS headlines, Redis-cached price data, and technical indicators to generate deterministic stock picks when all AI APIs fail.

### News and RSS Feed Sources (10 Feeds)
1. Google News India: 5 separate feeds covering Indian stock market, NSE stocks, Indian economy, stock market trading, and Nifty 50
2. Moneycontrol: 2 feeds for market news and stock analysis
3. Economic Times Markets: 1 feed for market and financial news
4. Mint Markets: 1 feed for business and market news
5. Business Standard Markets: 1 feed for market and company news

### Other Data Sources
- Wikipedia API: Company information and descriptions for the stock detail pages
- TradingView Lightweight Charts: Client-side charting library (not an API, but renders professional chart visuals)

---

## Platform and Infrastructure Services

### Hosting Platforms
1. Netlify: Hosts the Next.js 15 frontend web application. Auto-deploys from GitHub main branch. Currently has 70 remaining deploy credits (15 credits per deploy). Serves SSR pages with CDN distribution.
2. Railway: Hosts the FastAPI Python backend API and Redis cache. Auto-deploys from GitHub main branch using Docker or Nixpacks builds. Provides managed Redis instance.
3. Supabase: Hosts the PostgreSQL 16 database with TimescaleDB extension in ap-south-1 (Mumbai) region. Provides database management dashboard, SQL editor, and connection pooling.

### Development Tools
1. GitHub: Source control repository for the monorepo
2. Docker and Docker Compose: Local development environment orchestrating PostgreSQL, Redis, API, and web services
3. Claude Code CLI: AI-assisted development tool used to build the entire project. Uses MCP (Model Context Protocol) for browser automation, scheduled tasks, and Mermaid diagram generation.
4. Xcode 26.3: iOS app development and building

### Monitoring and Debugging
- Railway Logs: Backend application logs viewable in Railway dashboard
- Debug Endpoint (/api/ai-suggestions/debug): Custom production debugging endpoint showing Redis key counts, seed file status, headline matches, and cache info
- structlog JSON Logging: Structured production logs for every AI layer attempt

---

## Application Pages and Features

### Dashboard Page
The main landing page showing a real-time market overview. Contains stat cards displaying active breakouts count, triggered alerts count, volume surges, and market breadth percentage. Features an index ticker bar scrolling NIFTY 50, NIFTY BANK, NIFTY IT, and NIFTY MIDCAP 50 with live values. Includes a market breadth donut chart and a live breakout feed showing stocks hitting technical triggers.

### AI Picks Page
AI-generated stock recommendations organized into three timeframes: Intraday (5 picks for same-day trades), Weekly (5 picks for swing trades), and Monthly (5 picks for positional trades). Each pick includes the stock symbol, company name, entry price, target price, stop loss, rationale text, and confidence percentage. Powered by the 3-layer AI fallback system ensuring picks are always available.

### Screener Page
Contains 13 prebuilt technical scans: RSI Oversold (RSI below 30), RSI Overbought (RSI above 70), Bullish EMA Crossover (EMA9 crosses above EMA21), Bearish EMA Crossover (EMA9 crosses below EMA21), Price Above SMA200, Price Below SMA200, Volume Spike (volume 2x above average), Bollinger Squeeze (bandwidth contracting), MACD Bullish Cross, Near 52-Week High, ORB Breakout (Opening Range Breakout), Bullish Engulfing pattern, and a custom scan builder where users define their own indicator conditions with AND/OR logic.

### Charts Page
Interactive candlestick charts using TradingView Lightweight Charts v5. Supports timeframes: 1 minute, 5 minutes, 15 minutes, and 1 day. Overlay indicators include EMA 20, EMA 50, RSI 14, MACD (12,26,9), and Bollinger Bands (20,2). Volume panel displayed below the main chart. Company information panel shows Wikipedia-sourced company descriptions.

### Watchlist Page
User's personal stock tracking list with live prices. Add stocks via a search modal that filters the Nifty 500 universe. Each watchlist entry shows Last Traded Price (LTP), change percentage, volume, daily high, and daily low. Remove stocks with a single click.

### Alerts Page
Create price alerts on any stock. Set target price and direction (above/below). Triggered alerts appear in a timeline view. Alert triggers broadcast via WebSocket for real-time notification.

### Fundamentals Page
Filter and sort stocks by fundamental metrics: PE ratio, PB ratio, market cap, return on equity (ROE), dividend yield, and debt-to-equity ratio.

### Settings Page
User preferences and configuration options.

---

## AI Stock Picker System: 3-Layer Fallback Architecture

The AI stock picker is the flagship feature, designed to always return 15 stock recommendations (5 intraday, 5 weekly, 5 monthly) regardless of API availability.

### Layer 1: Google Gemini 2.0 Flash
Primary AI engine. Receives a prompt containing 40 parsed RSS news headlines and a market summary (NIFTY 50 level, top gainers/losers). Gemini analyzes news sentiment and market conditions to produce 15 stock picks with entry prices, targets, stop losses, and rationale. Uses primary API key first, falls back to backup key. Wrapped in a thread executor with 20-second timeout because Gemini's SDK blocks the Python event loop during internal retries on 429 (quota exceeded) errors.

### Layer 2: Groq Llama 3.3 70B and xAI Grok
Secondary AI engines activated when Gemini fails (quota exhausted, timeout, or invalid response). Same prompt and expected output format as Gemini. Groq provides approximately 500,000 free tokens per day with Llama 3.3 70B model. 25-second timeout.

### Layer 3: Technical Scoring Engine (Zero API Dependency)
Deterministic fallback that requires no external AI API. Process: (1) Load Nifty 500 stock list from nifty500_seed.json, (2) Scan 40 RSS headlines for stock symbol or company name mentions, (3) Bulk-read 461 price keys and 380 indicator keys from Redis using pipeline reads (2 round trips instead of 841 individual calls), (4) Score each stock on a 0-100 composite scale: News mentions (0-25 points), Price momentum (0-25 points), RSI signal (0-20 points), EMA crossover (0-15 points), Volume (0-15 points), (5) Apply timeframe-specific weight profiles, select top 5 per timeframe with no duplicates, (6) Generate template rationale strings. 15-second timeout.

### Caching Strategy
Generated suggestions are cached in Redis with a TTL set to expire at 9 AM the next trading day. The GET endpoint returns cached results instantly. If cache is empty, it returns a "pending" status and triggers background generation via FastAPI BackgroundTasks. Background generation has a 90-second global timeout.

---

## Data Flow Summary

External data flows into the system through multiple pipelines. The NSE Poller service runs every 30 seconds, fetching live prices from indianapi.in and writing them to Redis as price:{SYMBOL} keys with 300-second TTL. The Yahoo Finance service fetches historical OHLCV data and computes technical indicators (RSI 14, EMA 9, EMA 21, MACD, Bollinger Bands), storing results as ind:{SYMBOL}:1d hash keys in Redis with 600-second TTL. The AI Suggestions service aggregates 10 RSS news feeds, loads a market summary from Redis, and passes everything through the 3-layer AI chain. Results are cached in Redis. The frontend makes REST API calls to the FastAPI backend, which reads from Redis cache or Supabase PostgreSQL depending on the data type. WebSocket connections provide real-time price updates, scan progress, and alert triggers.

---

## Database Schema

### Supabase PostgreSQL Tables
1. stocks: Master stock data including symbol, company name, sector, industry, market cap. Seeded from nifty500_seed.json with 500 NSE symbols.
2. watchlist: User watchlist entries linking user IDs to stock symbols.
3. alerts: Price alert definitions with target price, direction, and active/triggered status.
4. ohlcv: Time-series candlestick data using TimescaleDB hypertables for efficient time-range queries. Stores 1-minute and daily candles.

### Redis Cache Keys
- price:{SYMBOL}: JSON string with LTP, change, change_pct, volume, high, low. 461 keys. 300s TTL.
- ind:{SYMBOL}:1d: Hash with rsi_14, ema_9, ema_21, macd, macd_signal, bb_upper, bb_lower, bb_mid. 380 keys. 600s TTL.
- ai:suggestions: JSON with 15 stock picks. TTL until 9 AM next trading day.
- market:indices: JSON with NIFTY 50, NIFTY BANK, NIFTY IT, NIFTY MIDCAP 50 levels.
- market:breadth: JSON with advances, declines, unchanged counts.

---

## API Endpoints

### Market Data
- GET /api/market/status: Market open/close status
- GET /api/market/breadth: Advances, declines, unchanged
- GET /api/market/sectors: Sector-wise performance
- GET /api/indices: Live index values

### Stock Data
- GET /api/stocks: Search and list stocks
- GET /api/prices/history: Historical OHLCV candles
- GET /api/prices/indicators: Technical indicators for a symbol
- GET /api/company/{symbol}: Company info from Wikipedia

### Screener
- POST /api/screener/run: Execute a custom scan with user-defined conditions
- GET /api/screener/prebuilt/{scan_name}: Run one of 13 prebuilt scans

### AI Suggestions
- GET /api/ai-suggestions: Get cached AI picks (returns instantly)
- POST /api/ai-suggestions/refresh: Force regeneration of AI picks
- GET /api/ai-suggestions/debug: Production debugging info

### User Features
- CRUD /api/watchlist: Add, list, remove watchlist stocks
- CRUD /api/alerts: Create, list, update, delete price alerts
- GET /api/fundamentals: Filter stocks by fundamental metrics

### Authentication
- GET /auth/upstox/login: Initiate Upstox OAuth2 flow
- GET /auth/upstox/callback: OAuth2 callback handler

---

## Design System

### Color Palette
- Background: Dark zinc/slate (#0a0a0a to #1a1a2e)
- Cards: Semi-transparent dark surfaces with subtle borders
- Positive/Up: Emerald green (#10b981)
- Negative/Down: Red (#ef4444)
- Accent: Purple gradient for branding
- Text: Gray-300 for body, white for headings

### Typography
- Font: System font stack (Inter/sans-serif)
- Monospace: For prices and numbers

### Component Patterns
- Terminal-inspired aesthetic with subtle glow effects
- Responsive design: Mobile-first with breakpoints at sm(640px), md(768px), lg(1024px)
- All data tables are sortable and filterable
- Toast notifications for user actions via Sonner
- Modal dialogs for stock search and confirmation

---

## Build and Development

### Local Development
Run the full stack locally with Docker Compose orchestrating PostgreSQL, Redis, the FastAPI backend, and the Next.js frontend. Backend runs on port 8000, frontend on port 3000.

### Deployment Pipeline
Push to GitHub main branch triggers automatic deployments: Railway builds and deploys the FastAPI backend using Docker, Netlify builds and deploys the Next.js frontend. No manual intervention needed.

### Seed Data
The nifty500_seed.json file contains metadata for 500 NSE stocks including symbol, company name, sector, and industry. This seeds both the PostgreSQL stocks table and provides the universe for the Layer 3 technical scoring engine.

---

## Project Timeline and Build Phases

### Phase 1: Foundation
Project setup with monorepo structure, FastAPI backend initialization, Next.js 15 frontend with React 19 and TypeScript, Docker Compose for local PostgreSQL and Redis, Supabase database schema creation.

### Phase 2: Data Pipeline
NSE Poller service with 30-second polling cycle, Redis cache layer for prices and indicators, Yahoo Finance integration for historical OHLCV, indicator engine computing RSI, EMA, MACD, Bollinger Bands, Nifty 500 seed data loading.

### Phase 3: Core Features
Dashboard with stat cards and index ticker, Screener engine with 13 prebuilt scans, Chart page using TradingView Lightweight Charts v5, Watchlist with add/remove and live prices, Alerts system with price triggers.

### Phase 4: AI Stock Picker
Gemini API integration with primary and backup keys, Groq API fallback with Llama 3.3 70B, RSS feed parser for 10 news sources, Technical scoring engine as zero-API fallback, 3-layer fallback chain ensuring picks always return, Background generation with instant GET response.

### Phase 5: Deployment
Railway backend auto-deploy from main, Netlify frontend with Next.js SSR, Redis on Railway with 461 cached price keys, iOS SwiftUI app with WebView wrapper.

### Phase 6: Production Hardening
Gemini thread executor fix (SDK blocks event loop), Redis pipeline reads (841 keys in 2 round trips), Global timeouts protecting every layer, Mobile UI fixes for iPhone viewport and touch, Debug endpoint for production troubleshooting.

---

## Key Architecture Decisions

1. Monorepo structure: All code (API, web, iOS) in one repository for unified deployment and shared configuration.
2. Redis-first caching: All frequently accessed data goes through Redis before database, reducing latency from seconds to milliseconds.
3. 3-layer AI fallback: Ensures the AI picks feature never returns empty, even during complete API outages.
4. Thread executor for Gemini: Google's SDK has internal retry logic that blocks Python's event loop. Wrapping sync calls in run_in_executor enables proper timeout cancellation.
5. Redis pipelines for bulk reads: Reading 841 keys individually over Railway's external Redis took over 60 seconds. Pipelines batch all reads into 2 round trips.
6. Background generation pattern: AI picks are generated in background tasks so the user-facing GET endpoint always returns instantly with either cached data or "pending" status.
7. TimescaleDB for OHLCV: Hypertables provide efficient time-range queries for candlestick data that would be slow with regular PostgreSQL tables.

---

## Technology Summary for Infographic

### Frontend Layer
Next.js 15, React 19, TypeScript, Tailwind CSS, Zustand, React Query, TradingView Lightweight Charts, Framer Motion, Recharts, Lucide Icons, React Hook Form, Zod, Sonner

### Backend Layer
FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic, Uvicorn, Pydantic, httpx, feedparser, yfinance, structlog, Google Generative AI SDK, Groq SDK

### Data Layer
PostgreSQL 16 with TimescaleDB, Redis 7, Supabase, Nifty 500 seed JSON

### AI and LLM Services
Google Gemini 2.0 Flash, Groq Llama 3.3 70B, xAI Grok, Custom Technical Scoring Engine

### External Data APIs
NSE via indianapi.in, Yahoo Finance, Upstox WebSocket, NSE Direct Scraping, Wikipedia API

### News Sources (10 RSS Feeds)
Google News India (5 feeds), Moneycontrol (2 feeds), Economic Times (1 feed), Mint (1 feed), Business Standard (1 feed)

### Hosting Platforms
Netlify (frontend), Railway (backend and Redis), Supabase (database)

### Mobile
SwiftUI, WKWebView, Swift 5.9, Xcode 26.3

### DevOps
GitHub, Docker, Docker Compose, Railway Auto-Deploy, Netlify Auto-Deploy

### Development Tools
Claude Code CLI with MCP, Mermaid.js for diagrams, Figma for design
