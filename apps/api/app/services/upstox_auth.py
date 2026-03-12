"""Upstox OAuth2 flow helpers."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx
import structlog

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from app.services.redis_cache import get_redis, set_with_ttl
from app.utils.redis_keys import KEY_UPSTOX_TOKEN, TTL_TOKEN

log = structlog.get_logger(__name__)

_AUTHORIZE_URL = "https://api.upstox.com/v2/login/authorization/dialog"
_TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"


class UpstoxAuthError(BreakoutScanError):
    """Raised when an Upstox authentication operation fails."""


def get_login_url(state: str = "") -> str:
    """Build the Upstox authorize URL that the user should be redirected to.

    Parameters
    ----------
    state:
        An opaque string passed through the OAuth redirect for CSRF protection.
    """
    settings = get_settings()
    params = {
        "client_id": settings.upstox_api_key,
        "redirect_uri": settings.upstox_redirect_uri,
        "response_type": "code",
    }
    if state:
        params["state"] = state
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> str:
    """Exchange an authorization *code* for an access token.

    Returns the access token string and persists it in Redis.

    Raises :class:`UpstoxAuthError` on failure.
    """
    settings = get_settings()
    payload = {
        "code": code,
        "client_id": settings.upstox_api_key,
        "client_secret": settings.upstox_api_secret,
        "redirect_uri": settings.upstox_redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            _TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        log.error("upstox_token_exchange_failed", status=resp.status_code, body=resp.text)
        raise UpstoxAuthError(f"Token exchange failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    access_token: str = data["access_token"]
    await store_token(access_token)
    log.info("upstox_token_stored")
    return access_token


async def store_token(token: str) -> None:
    """Persist *token* in Redis with the market-session TTL (8 h)."""
    await set_with_ttl(KEY_UPSTOX_TOKEN, token, TTL_TOKEN)


async def get_token() -> str | None:
    """Retrieve the current Upstox access token from Redis.

    Returns ``None`` when no valid token exists (re-login required).
    """
    r = await get_redis()
    return await r.get(KEY_UPSTOX_TOKEN)


async def is_token_valid() -> bool:
    """Return ``True`` if an access token is present in Redis."""
    return (await get_token()) is not None


async def refresh_token() -> None:
    """Upstox does not support refresh tokens.

    This function logs a warning so callers can react and prompt the user
    to re-authenticate.

    Raises :class:`UpstoxAuthError` unconditionally.
    """
    log.warning("upstox_refresh_not_supported", hint="User must re-login via OAuth")
    raise UpstoxAuthError("Upstox does not support token refresh; re-login is required.")
