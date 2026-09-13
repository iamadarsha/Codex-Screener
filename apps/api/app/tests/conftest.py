"""Shared pytest fixtures.

Built from scratch this session — previously there was no conftest.py, no
async test client, no Redis fixture, and pytest-asyncio had no mode
configured (see docs/ARCHITECTURE_AUDIT.md). `asyncio_mode = auto` is set
in apps/api/pytest.ini so async tests don't need `@pytest.mark.asyncio`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import fakeredis.aioredis
import httpx
import pytest

import app.services.redis_cache as redis_cache


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    """A real (fake) Redis instance, wired into app.services.redis_cache's
    global pool so any code calling `get_redis()` during the test gets it,
    without needing an actual Redis server."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    previous_pool = redis_cache._pool  # noqa: SLF001
    redis_cache._pool = fake  # noqa: SLF001
    try:
        yield fake
    finally:
        await fake.aclose()
        redis_cache._pool = previous_pool  # noqa: SLF001


@pytest.fixture
def research_runs_root(tmp_path, monkeypatch):
    """Point `app.research.artifacts.resolve_run_dir` at an isolated tmp
    directory instead of the real `./research_runs`, so research-package
    tests never touch the actual working tree. Yields the root Path."""
    from app.core.config import Settings

    root = tmp_path / "research_runs"
    fake_settings = Settings(research_runs_root=str(root))
    monkeypatch.setattr("app.research.artifacts.get_settings", lambda: fake_settings)
    return root


@pytest.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    """An async HTTP client wired directly to the FastAPI app (no network)."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
