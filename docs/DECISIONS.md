# Architecture Decision Records — Codex Screener

## ADR-001: Python Dependency Pinning {#dep-pinning}

**Date:** 2026-03-23
**Status:** Accepted

### Context

Railway's Starter plan has ~512 MB memory. An unpinned `pip install` on a fresh build
installed `pandas 3.0.1 + numpy 2.4.3`, which caused OOM during container startup.
The site returned 502 with "market is closed" because the API never came up.

### Decision

Pin all Python dependencies with `>=min,<next-major` ranges in `requirements.txt`.
Never use bare package names.

Key constraints:
```
numpy>=2.2.6,<3.0.0     # required by pandas-ta 0.4.x
pandas>=2.2.0,<3.0.0    # pandas 3.x causes OOM on Railway 512MB
pandas-ta>=0.4.67b0,<0.5.0b0  # only 0.4.67b0 and 0.4.71b0 exist on PyPI
```

Note: `pandas-ta==0.3.14b0` **does not exist on PyPI**. Only 0.4.x versions are available.

### Consequences

- Builds are reproducible and memory-safe.
- Dependency upgrades require deliberate version bumps and local Docker testing.

---

## ADR-002: slowapi for Rate Limiting

**Date:** 2026-03-23
**Status:** Accepted

### Context

The API had no rate limiting. A burst of frontend requests or a bot could exhaust
Supabase connection limits or Gemini API quota.

### Decision

Use `slowapi` (starlette-compatible limiter) with `get_remote_address` key.
Limits configured via env vars for runtime adjustment without redeployment.

### Consequences

- All routes decorated with `@limiter.limit(...)`.
- 429 responses handled by `_rate_limit_exceeded_handler`.
- Limits adjustable via Railway dashboard without code changes.

---

## ADR-003: NSE Poller Watchdog

**Date:** 2026-03-23
**Status:** Accepted

### Context

`nse_poller_loop()` occasionally crashed due to NSE's unofficial API returning
unexpected responses. When it crashed, market data stopped updating silently.

### Decision

Wrap `nse_poller_loop()` in `_poller_watchdog()` — an infinite async loop with
exponential back-off (5s → 10s → 20s → … capped at 300s). Track `_poller_running`
flag for the `/health` endpoint to surface poller status.

### Consequences

- Poller self-heals after transient NSE failures.
- Health endpoint shows poller state for Railway uptime monitoring.
- Persistent crashes are visible in logs with back-off times.

---

## ADR-004: Async Supabase via asyncpg + SQLAlchemy 2.0

**Date:** (prior to 2026-03)
**Status:** Accepted

### Context

Supabase uses PgBouncer on port 6543 for connection pooling. asyncpg's prepared
statement cache is incompatible with PgBouncer in transaction mode.

### Decision

Use `create_async_engine` with `connect_args={"prepared_statement_cache_size": 0}`.
Always use port `6543` (PgBouncer), not `5432` (direct).

### Consequences

- No prepared statement errors in production.
- Slight performance overhead (no client-side stmt cache), acceptable for this scale.

---

## ADR-005: AI Fallback Chain

**Date:** (prior to 2026-03)
**Status:** Accepted

### Context

Gemini API occasionally hits quota limits, especially around Indian market open (9:15 AM IST).

### Decision

Three-tier AI fallback: Gemini → Groq → xAI Grok.
On all-tier failure: return last cached analysis or empty response.

### Consequences

- AI analysis almost always available during market hours.
- Three separate API keys required in Railway env.
- Cost hierarchy: Gemini (cheapest) → Groq → xAI (most expensive).

---

## ADR-006: Frontend Null-Safe Market Status

**Date:** 2026-03-23
**Status:** Accepted

### Context

When the API is down, `fetch('/api/health')` returns a network error. The frontend
previously threw an uncaught error and showed a broken UI.

### Decision

All market status reads use `status?.is_open ?? false`. This defaults to "Closed"
when the API is unreachable, which is accurate (can't trade without data) and clean.

```typescript
const isOpen = status?.is_open ?? false
```

### Consequences

- UI is always functional even when API is down.
- "Market Closed" shown during API downtime — acceptable UX trade-off.
