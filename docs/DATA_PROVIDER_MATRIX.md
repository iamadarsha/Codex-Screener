# Data Provider Matrix

Verified directly against each provider's current official documentation on
2026-09-13. Re-verify before relying on any of these numbers in production —
pricing, limits, and terms change without notice.

## Market data

| Provider | Role | Auth | Current limits/terms | Status in code |
|---|---|---|---|---|
| **Upstox V3 WebSocket feed** | Primary realtime tick data | Bearer token (Analytics Token preferred) | Binary Protobuf (schema in `apps/api/app/market/proto/MarketDataFeed.proto`, downloaded verbatim from Upstox). `sub`/`unsub`/`change_mode`. Modes: `ltpc` (5000-key cap, no cumulative volume), `full_d5` — labeled "full" in Upstox's docs/UI (2000-key cap, includes `vtt` cumulative day volume), `option_greeks` (3000), `full_d30` (50, Upstox Plus only). Requires a separate REST "authorize" call (`GET /v3/feed/market-data-feed/authorize`) that returns a single-use `wss://` URL. First message on connect is `market_info` (segment status), then live ticks. | ✅ Implemented in `apps/api/app/market/` (Milestone 2.1) — protobuf decode, tick normalization, candle/indicator pipeline, all unit-tested against synthetic fixtures. ⚠️ **Never tested against a live connection** — no Upstox credentials available this round. See `docs/UPSTOX_ONBOARDING.md`. |
| **Upstox Analytics Token** | Preferred auth for the owner-controlled backend | Generated from Developer Apps page, no OAuth redirect | Read-only, 1-year validity, one active token per account. Covers market quotes, historical data, option chains, fundamentals, news, websocket (no static IP needed for these). Free. | ✅ Supported in code (`Settings.upstox_analytics_token`, preferred by `upstox_auth.get_bearer_token()`) — falls back to the existing OAuth2 flow if unset. ⚠️ Not yet generated/tested — see `docs/UPSTOX_ONBOARDING.md`. |
| **NSE India direct (public JSON endpoints)** | Fallback / current live price source | None (cookie-based session) | Undocumented, unofficial, rate-limit-sensitive — must use polite polling, caching, and backoff. Current NSE Data Sharing & Usage Policy: https://www.nseindia.com/static/market-data/nse-data-policy | ✅ This is actually the **primary** live source today (`nse_poller.py`, 30s REST poll), not a fallback — the realtime WebSocket path isn't wired in. |
| **Yahoo Finance (`yfinance`)** | Historical OHLCV for indicator computation | None | Explicitly positioned by the maintainers as research/educational; consult Yahoo's own terms before relying on it for a production, user-facing redistribution use case. | ✅ Used for indicator computation (`yahoo_finance.py`) — should stay a research/history fallback only, not become the realtime spine (matches master prompt guidance). |
| **stock.indianapi.in** | Trending stocks, fundamentals fallback | API key header | Third-party paid service; current pricing/limits not independently re-verified this session — check your dashboard. | ✅ Used (`indian_api.py`) for trending + fundamentals. |

## AI / LLM

| Provider | Role | Model in code | Notes |
|---|---|---|---|
| Google Gemini | Layer 2 of the 3-layer AI Trade Brief fallback | `gemini-2.5-flash-lite` | Via `google-genai` SDK, with a backup key fallback. |
| Groq | Layer 3 fallback | `llama-3.3-70b-versatile` | Via `groq` SDK. |
| xAI (Grok) | Further fallback if Groq fails | Raw HTTP call | `xai_api_key` in config. |

Layer 1 (local technical scoring, zero external API cost) actually fires
first in the real fallback order — see `apps/api/app/services/ai_suggestions.py`.

## Infrastructure

| Provider | Role | Current terms (verified 2026-09-13) | Decision |
|---|---|---|---|
| **Fly.io** | Considered for backend hosting last session | Free tier removed for new orgs since Oct 2024 — new accounts get a 2-VM-hour/7-day trial, then pay-as-you-go (~$2-5/mo for one always-on shared-cpu-1x machine). Legacy orgs (pre-Oct 2024) may retain the old free allowance. | ❌ Rejected as the primary target — not actually free for a new account. `fly.toml`/`deploy_fly.sh` kept as reference only. |
| **Oracle Cloud Always Free (Ampere A1.Flex)** | Chosen backend host | 2 OCPU / 12GB RAM total (flexible split across instances), 200GB block storage, 10TB/month egress, 50Mbps public IPv4 bandwidth. Idle-instance reclamation risk if CPU/network/memory utilization stays under 20% for 7+ days — a continuously-polling backend should not trigger this. Regional capacity can be constrained ("out of host capacity" errors are common; retry a different availability domain). | ✅ Chosen. User does not yet have an Oracle Cloud account — needs signup + card-on-file (Always Free tier isn't charged) before VM provisioning can start. |
| **Vercel** | Frontend hosting | Free (Hobby) tier — already deployed and live. | ✅ Live at `https://breakoutscan-web.vercel.app`. |
| **Supabase** | Postgres + Auth + RLS | Free tier: 500MB DB, 1GB file storage, 5GB egress, 50k MAU, possible pause after 7 days of inactivity. | ✅ Already in use, no migration needed. |
| **Cloudflare R2** | Historical Parquet / backups (not yet used) | 10GB-month storage free, 1M Class A + 10M Class B requests/month free, free egress. | Not yet provisioned — relevant once historical/replay datasets exist (Phase 5). |

## Reference libraries evaluated (not yet adopted)

| Library | Purpose | Status |
|---|---|---|
| TA-Lib (`ta-lib-python`) | 150+ indicators, candlestick patterns, BSD-2-Clause | Not used; pandas-ta is used throughout today. Migration is a Phase 2/3 decision. |
| Polars | Bulk historical processing, replay, backtests | Not used; pandas is used throughout. |
| Valkey | Redis-protocol-compatible cache/pubsub, self-hostable | Not used; `redis-py` against a hosted Redis is used today. |
| jugaad-data | NSE fallback/reference, historical ingestion aid | Not used; `nse_fallback.py`'s own scraping client is the current NSE fallback. |
