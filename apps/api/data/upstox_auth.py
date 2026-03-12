from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.parse import urlencode

import redis.asyncio as redis
import upstox_client
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.errors import BreakoutScanError

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["upstox-auth"])

UPSTOX_TOKEN_KEY = "upstox:token"
UPSTOX_TOKEN_META_KEY = "upstox:token:meta"
UPSTOX_STATE_PREFIX = "upstox:oauth_state:"
UPSTOX_AUTHORIZE_BASE = "https://api.upstox.com/v2/login/authorization/dialog"

_redis_client: redis.Redis[str] | None = None


class UpstoxAuthError(BreakoutScanError):
    """Raised when the Upstox OAuth flow fails."""


class UpstoxTokenMissingError(UpstoxAuthError):
    """Raised when a cached Upstox token is required but missing."""


@dataclass(slots=True)
class UpstoxTokenSnapshot:
    access_token: str
    user_id: str | None
    user_name: str | None
    email: str | None
    broker: str | None
    issued_at: str

    def to_redis_mapping(self) -> dict[str, str]:
        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None and value != ""
        }


def get_redis_client() -> redis.Redis[str]:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def build_authorize_url(state: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.upstox_api_key,
            "redirect_uri": settings.upstox_redirect_uri,
            "state": state,
        }
    )
    return f"{UPSTOX_AUTHORIZE_BASE}?{query}"


def build_api_client(access_token: str | None = None) -> upstox_client.ApiClient:
    configuration = upstox_client.Configuration()
    if access_token:
        configuration.access_token = access_token
    api_client = upstox_client.ApiClient(configuration=configuration)
    return api_client


async def store_oauth_state(state: str) -> None:
    redis_client = get_redis_client()
    try:
        await redis_client.set(
            f"{UPSTOX_STATE_PREFIX}{state}",
            "1",
            ex=settings.redis_oauth_state_ttl_seconds,
        )
    except redis.RedisError as error:
        raise UpstoxAuthError("Unable to cache the OAuth state in Redis.") from error


async def validate_oauth_state(state: str | None) -> None:
    if state is None or state == "":
        raise UpstoxAuthError("Missing OAuth state from callback.")

    redis_client = get_redis_client()

    try:
        exists = await redis_client.getdel(f"{UPSTOX_STATE_PREFIX}{state}")
    except redis.RedisError as error:
        raise UpstoxAuthError("Unable to validate the OAuth state from Redis.") from error

    if exists is None:
        raise UpstoxAuthError("OAuth state expired or does not match the login request.")


def exchange_code_for_token_sync(code: str) -> UpstoxTokenSnapshot:
    try:
        api_client = build_api_client()
        login_api = upstox_client.LoginApi(api_client)
        token_response = login_api.token(
            settings.upstox_api_version,
            code=code,
            client_id=settings.upstox_api_key,
            client_secret=settings.upstox_api_secret,
            redirect_uri=settings.upstox_redirect_uri,
            grant_type="authorization_code",
        )
    except Exception as error:
        raise UpstoxAuthError("Upstox rejected the authorization code exchange.") from error

    issued_at = datetime.now(tz=UTC).isoformat()

    return UpstoxTokenSnapshot(
        access_token=str(token_response.access_token),
        user_id=cast(str | None, getattr(token_response, "user_id", None)),
        user_name=cast(str | None, getattr(token_response, "user_name", None)),
        email=cast(str | None, getattr(token_response, "email", None)),
        broker=cast(str | None, getattr(token_response, "broker", None)),
        issued_at=issued_at,
    )


async def exchange_code_for_token(code: str) -> UpstoxTokenSnapshot:
    try:
        token_snapshot = await asyncio.to_thread(exchange_code_for_token_sync, code)
    except UpstoxAuthError:
        raise
    except Exception as error:
        raise UpstoxAuthError("Unexpected error while exchanging the authorization code.") from error

    return token_snapshot


async def persist_token_snapshot(snapshot: UpstoxTokenSnapshot) -> None:
    redis_client = get_redis_client()

    try:
        pipeline = redis_client.pipeline()
        pipeline.set(
            UPSTOX_TOKEN_KEY,
            snapshot.access_token,
            ex=settings.redis_token_ttl_seconds,
        )
        pipeline.hset(UPSTOX_TOKEN_META_KEY, mapping=snapshot.to_redis_mapping())
        pipeline.expire(UPSTOX_TOKEN_META_KEY, settings.redis_token_ttl_seconds)
        await pipeline.execute()
    except redis.RedisError as error:
        raise UpstoxAuthError("Unable to persist the Upstox access token in Redis.") from error


async def load_token_snapshot() -> UpstoxTokenSnapshot | None:
    redis_client = get_redis_client()

    try:
        access_token, metadata = await asyncio.gather(
            redis_client.get(UPSTOX_TOKEN_KEY),
            redis_client.hgetall(UPSTOX_TOKEN_META_KEY),
        )
    except redis.RedisError as error:
        raise UpstoxAuthError("Unable to read the cached Upstox token from Redis.") from error

    if access_token is None:
        return None

    return UpstoxTokenSnapshot(
        access_token=access_token,
        user_id=metadata.get("user_id"),
        user_name=metadata.get("user_name"),
        email=metadata.get("email"),
        broker=metadata.get("broker"),
        issued_at=metadata.get("issued_at", ""),
    )


async def get_access_token(required: bool = True) -> str | None:
    snapshot = await load_token_snapshot()
    if snapshot is None:
        if required:
            raise UpstoxTokenMissingError(
                "No Upstox token is cached. Visit /auth/login to complete OAuth."
            )
        return None
    return snapshot.access_token


def validate_token_sync(access_token: str) -> str:
    try:
        api_client = build_api_client(access_token)
        websocket_api = upstox_client.WebsocketApi(api_client)
        response = websocket_api.get_market_data_feed_authorize_v3()
    except Exception as error:
        raise UpstoxAuthError("Unable to validate the cached Upstox token.") from error

    authorized_uri = cast(str | None, getattr(response.data, "authorized_redirect_uri", None))
    if authorized_uri is None or authorized_uri == "":
        raise UpstoxAuthError("Upstox did not return an authorized market-feed URI.")

    return authorized_uri


async def validate_token(access_token: str) -> str:
    try:
        return await asyncio.to_thread(validate_token_sync, access_token)
    except UpstoxAuthError:
        raise
    except Exception as error:
        raise UpstoxAuthError("Unexpected error while validating the cached token.") from error


async def refresh_cached_token() -> dict[str, str]:
    snapshot = await load_token_snapshot()
    if snapshot is None:
        raise UpstoxTokenMissingError(
            "No Upstox token is cached. Manual login is required before refresh."
        )

    authorized_uri = await validate_token(snapshot.access_token)
    await persist_token_snapshot(snapshot)

    return {
        "status": "validated",
        "authorized_feed_uri": authorized_uri,
        "user_id": snapshot.user_id or "",
    }


def build_login_payload(state: str) -> dict[str, str]:
    return {
        "status": "pending_login",
        "authorize_url": build_authorize_url(state),
        "redirect_uri": settings.upstox_redirect_uri,
        "state": state,
    }


async def prepare_login() -> dict[str, str]:
    state = secrets.token_urlsafe(24)
    await store_oauth_state(state)
    return build_login_payload(state)


@router.get("/auth/login", response_model=None)
@router.get("/auth/upstox/login", response_model=None)
async def auth_login(
    redirect: bool = Query(default=False),
) -> RedirectResponse | dict[str, str]:
    if settings.upstox_api_key == "" or settings.upstox_api_secret == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UPSTOX_API_KEY and UPSTOX_API_SECRET must be configured.",
        )

    try:
        payload = await prepare_login()
    except UpstoxAuthError as error:
        logger.exception("upstox login setup failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

    if redirect:
        return RedirectResponse(url=payload["authorize_url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    return payload


@router.get("/auth/callback")
@router.get("/auth/upstox/callback")
async def auth_callback(
    code: str = Query(..., min_length=1),
    state: str | None = Query(default=None),
) -> dict[str, str]:
    try:
        await validate_oauth_state(state)
        snapshot = await exchange_code_for_token(code)
        await persist_token_snapshot(snapshot)
        authorized_uri = await validate_token(snapshot.access_token)
    except UpstoxAuthError as error:
        logger.exception("upstox callback failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return {
        "status": "authenticated",
        "user_id": snapshot.user_id or "",
        "user_name": snapshot.user_name or "",
        "email": snapshot.email or "",
        "authorized_feed_uri": authorized_uri,
    }


@router.get("/auth/status")
async def auth_status() -> dict[str, str | bool]:
    try:
        snapshot = await load_token_snapshot()
        if snapshot is None:
            return {
                "authenticated": False,
                "redirect_uri": settings.upstox_redirect_uri,
            }

        authorized_uri = await validate_token(snapshot.access_token)
    except UpstoxAuthError as error:
        logger.warning("upstox auth status validation failed: %s", error)
        return {
            "authenticated": False,
            "redirect_uri": settings.upstox_redirect_uri,
            "error": str(error),
        }

    return {
        "authenticated": True,
        "user_id": snapshot.user_id or "",
        "user_name": snapshot.user_name or "",
        "email": snapshot.email or "",
        "issued_at": snapshot.issued_at,
        "redirect_uri": settings.upstox_redirect_uri,
        "authorized_feed_uri": authorized_uri,
    }


@router.post("/auth/refresh")
async def auth_refresh() -> dict[str, str]:
    try:
        return await refresh_cached_token()
    except UpstoxAuthError as error:
        logger.exception("upstox token refresh failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
