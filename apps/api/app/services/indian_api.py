"""Async client for the Indian Stock API (https://stock.indianapi.in)."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.core.config import get_settings

log = structlog.get_logger(__name__)

_BASE_URL = "https://stock.indianapi.in"


class IndianAPIClient:
    """Thin async wrapper around the Indian Stock API.

    Uses lazy client initialisation identical to :class:`NSEClient` so the
    ``httpx.AsyncClient`` is only created on the first real request.
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create the HTTP client with the required API-key header."""
        if self._client is None or self._client.is_closed:
            settings = get_settings()
            api_key = settings.indian_api_key
            if not api_key:
                log.warning("indian_api_key is not configured; requests will likely fail")

            self._client = httpx.AsyncClient(
                base_url=_BASE_URL,
                headers={
                    "X-Api-Key": api_key,
                    "Accept": "application/json",
                },
                timeout=20,
                follow_redirects=True,
            )
            log.info("indian_api_client_created")
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            log.info("indian_api_client_closed")

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the parsed JSON body."""
        client = await self._ensure_client()
        try:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            log.warning(
                "indian_api_http_error",
                path=path,
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            return {}
        except httpx.HTTPError as exc:
            log.warning("indian_api_request_error", path=path, error=str(exc))
            return {}

    # ------------------------------------------------------------------
    # Public endpoints
    # ------------------------------------------------------------------

    async def get_stocks(self) -> list[dict[str, Any]]:
        """GET /stocks -- returns a list of stock data."""
        data = await self._get("/stocks")
        if isinstance(data, list):
            return data
        # Some endpoints wrap the list in a dict
        if isinstance(data, dict):
            return data.get("data", data.get("stocks", []))
        return []

    async def get_stock(self, symbol: str) -> dict[str, Any]:
        """GET /stock?name={symbol} -- returns details for a single stock."""
        data = await self._get("/stock", params={"name": symbol})
        return data if isinstance(data, dict) else {}

    async def get_ipo(self) -> Any:
        """GET /ipo -- returns IPO data."""
        return await self._get("/ipo")

    async def get_mutual_funds(self) -> Any:
        """GET /mutualfunds -- returns mutual fund data."""
        return await self._get("/mutualfunds")

    async def get_trending(self) -> Any:
        """GET /trending -- returns trending stocks."""
        return await self._get("/trending")
