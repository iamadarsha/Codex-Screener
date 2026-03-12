"""NSE website API fallback client for when the WebSocket feed is down."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.services.redis_cache import get_value
from app.utils.redis_keys import KEY_WS_LAST_TICK
from app.utils.retry import async_retry
from app.utils.time import now_ist

log = structlog.get_logger(__name__)

_BASE_URL = "https://www.nseindia.com"
_SILENCE_THRESHOLD_SECONDS = 60

# NSE blocks bots aggressively; these headers are the bare minimum to
# survive cookie-gated endpoints.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
}


class NSEClient:
    """Thin async wrapper around NSE's public JSON endpoints.

    Manages cookies and headers to handle NSE anti-bot protections.
    A fresh session cookie is obtained transparently before data requests.
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create and warm up the HTTP client with a session cookie."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=_BASE_URL,
                headers=_DEFAULT_HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            await self._refresh_cookies()
        return self._client

    async def _refresh_cookies(self) -> None:
        """Hit the NSE homepage to obtain fresh session cookies."""
        if self._client is None:
            return
        try:
            resp = await self._client.get("/")
            log.debug("nse_cookies_refreshed", status=resp.status_code)
        except httpx.HTTPError as exc:
            log.warning("nse_cookie_refresh_failed", error=str(exc))

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Data endpoints
    # ------------------------------------------------------------------

    @async_retry(max_attempts=2, min_wait=1.0, max_wait=5.0)
    async def get_indices(self) -> dict[str, Any]:
        """Fetch ``/api/allIndices`` which lists all NSE index values."""
        client = await self._ensure_client()
        resp = await client.get("/api/allIndices")
        if resp.status_code == 403:
            await self._refresh_cookies()
            resp = await client.get("/api/allIndices")
        resp.raise_for_status()
        return resp.json()

    @async_retry(max_attempts=2, min_wait=1.0, max_wait=5.0)
    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch equity quote for *symbol* from ``/api/quote-equity``."""
        client = await self._ensure_client()
        resp = await client.get("/api/quote-equity", params={"symbol": symbol})
        if resp.status_code == 403:
            await self._refresh_cookies()
            resp = await client.get("/api/quote-equity", params={"symbol": symbol})
        resp.raise_for_status()
        return resp.json()

    @async_retry(max_attempts=2, min_wait=1.0, max_wait=5.0)
    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        """Fetch the option chain for *symbol*."""
        client = await self._ensure_client()
        resp = await client.get("/api/option-chain-equities", params={"symbol": symbol})
        if resp.status_code == 403:
            await self._refresh_cookies()
            resp = await client.get(
                "/api/option-chain-equities", params={"symbol": symbol}
            )
        resp.raise_for_status()
        return resp.json()


async def is_fallback_needed() -> bool:
    """Return ``True`` if the WebSocket feed appears stale.

    Checks ``ws:last_tick_at`` in Redis.  If it is missing or older than
    60 seconds the fallback is needed.
    """
    raw = await get_value(KEY_WS_LAST_TICK)
    if raw is None:
        return True

    from datetime import datetime

    try:
        last_tick = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return True

    delta = (now_ist() - last_tick).total_seconds()
    return delta > _SILENCE_THRESHOLD_SECONDS
