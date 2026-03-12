"""Redis async singleton with convenience helpers."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

log = structlog.get_logger(__name__)

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return (and lazily create) the global :class:`aioredis.Redis` instance."""
    global _pool  # noqa: PLW0603
    if _pool is None:
        settings = get_settings()
        _pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        log.info("redis_connected", url=settings.redis_url)
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool  # noqa: PLW0603
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        log.info("redis_closed")


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


async def set_with_ttl(key: str, value: str, ttl: int) -> None:
    """SET *key* to *value* with an expiry of *ttl* seconds."""
    r = await get_redis()
    await r.set(key, value, ex=ttl)


async def get_value(key: str) -> str | None:
    """GET a plain string value."""
    r = await get_redis()
    return await r.get(key)


async def set_json(key: str, obj: Any, ttl: int | None = None) -> None:
    """Serialize *obj* as JSON and store under *key*."""
    r = await get_redis()
    payload = json.dumps(obj, default=str)
    if ttl is not None:
        await r.set(key, payload, ex=ttl)
    else:
        await r.set(key, payload)


async def get_json(key: str) -> Any | None:
    """Retrieve and deserialize a JSON value. Returns ``None`` on miss."""
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def hset_dict(key: str, mapping: dict[str, Any], ttl: int | None = None) -> None:
    """Write a full dict into a Redis hash, optionally setting a TTL."""
    r = await get_redis()
    str_mapping = {k: str(v) for k, v in mapping.items()}
    await r.hset(key, mapping=str_mapping)
    if ttl is not None:
        await r.expire(key, ttl)


async def hget_all(key: str) -> dict[str, str]:
    """Return all fields of a Redis hash."""
    r = await get_redis()
    return await r.hgetall(key)


async def publish(channel: str, message: str) -> int:
    """Publish *message* to a Redis Pub/Sub *channel*.

    Returns the number of subscribers that received the message.
    """
    r = await get_redis()
    return await r.publish(channel, message)


async def subscribe(channel: str) -> aioredis.client.PubSub:
    """Return an :class:`aioredis.client.PubSub` subscribed to *channel*.

    Caller is responsible for iterating and closing the subscription.
    """
    r = await get_redis()
    ps = r.pubsub()
    await ps.subscribe(channel)
    return ps
