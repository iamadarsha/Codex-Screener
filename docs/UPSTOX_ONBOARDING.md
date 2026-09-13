# Getting Upstox access for Milestone 2.2 (live realtime testing)

The Phase 2 engine (`apps/api/app/market/`) is built and unit-tested against
synthetic fixtures, but has never been exercised against a real Upstox
connection — you currently have no Upstox Developer App or Analytics Token.
This is what unblocks Milestone 2.2.

## What I could and couldn't confirm from public docs

Upstox's public documentation doesn't state outright whether generating an
Analytics Token requires an existing funded/KYC'd Upstox trading account, or
just a registered developer account — I won't guess. You'll find out when
you try the steps below.

## Path A — Analytics Token (recommended, no OAuth browser flow)

1. Go to **https://account.upstox.com/developer/apps**.
2. Log in with your Upstox account.
3. Check whether an app already exists — the repo's `.env`/Fly secrets
   already had an `UPSTOX_API_KEY`/`UPSTOX_API_SECRET` pair from a prior
   session, which implies a Developer App was created before. If so, open
   it and look for an **Analytics** tab.
4. If an Analytics tab exists: click **Generate Token**, confirm, and copy
   the value. It's valid for 1 year, read-only, free.
5. If no app exists yet: create one (name + redirect URI — the redirect URI
   doesn't matter for the Analytics Token path since it skips OAuth, but
   Upstox's form may still require one; `https://breakoutscan-web.vercel.app`
   is fine as a placeholder).
6. Add it to `apps/api/.env` (and to your deployed backend's env once you
   have one) as `UPSTOX_ANALYTICS_TOKEN=...` — this is read by
   `Settings.upstox_analytics_token` (`apps/api/app/core/config.py`) and
   preferred automatically by `upstox_auth.get_bearer_token()`.

## Path B — existing OAuth2 API key/secret (fallback, needs one browser click)

If Path A turns out to need something you don't have, the OAuth2 key/secret
already in the repo's config still works (not rotated, per your decision in
Phase 1 — see `docs/SECURITY_REMEDIATION.md`):

1. Start the backend locally or on whatever host is live.
2. Visit `/auth/login` — it redirects you to Upstox's login page
   (`app/api/routes/auth.py` → `upstox_auth.get_login_url()`).
3. Log in and approve the app.
4. You're redirected back to `/auth/upstox/callback`, which exchanges the
   code for an access token and stores it in Redis
   (`upstox_auth.exchange_code`). No Analytics Token needed for this path.
5. Note: this token has **no refresh mechanism** (`upstox_auth.refresh_token()`
   raises unconditionally) — you'll need to repeat this once the session
   expires (Upstox tokens are typically valid until end-of-day).

## Once you have either one

Tell me which path worked and I'll:
1. Do a real connectivity smoke test against `apps/api/app/market/provider.py`.
2. Verify the V3 subscription (`full_d5` mode, NIFTY 500 universe) actually
   works within the 2000-key cap.
3. Test reconnect/resubscribe against the live connection.
4. Verify `ltq`/`vtt` field values against real market data (ideally during
   NSE hours, 9:15–15:30 IST).
5. Wire `UpstoxV3Provider` into `main.py`'s lifespan as primary, with
   `nse_poller.py` demoted to automatic fallback via
   `apps/api/app/market/failover.py`'s state machine.
6. Delete the now-fully-superseded `upstox_streamer.py`, `candle_builder.py`,
   `indicator_engine.py`.
