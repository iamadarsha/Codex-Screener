from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_engine = None
_session_factory = None


def _get_engine():
    """Lazily create the SQLAlchemy async engine on first use."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict = {}
        if "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url:
            connect_args["ssl"] = "require"
        # Disable prepared statement caching for PgBouncer transaction-mode poolers
        # (Supabase port 6543 uses PgBouncer in transaction mode, which doesn't
        # support named prepared statements that asyncpg sends by default).
        if ":6543" in settings.database_url:
            connect_args["statement_cache_size"] = 0
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_timeout=10,
            pool_recycle=300,
            # Kept well under Supabase's free-tier Session Pooler cap
            # (Supavisor: 15 concurrent connections, PROJECT-wide, not
            # per-process). The old 5+10=15 setting let this single API
            # process alone claim the entire project quota — confirmed
            # live (2026-09-15): running one `alembic upgrade` alongside
            # the running app hit "max clients reached in session mode"
            # immediately.
            #
            # An initial 3+2=5 was too tight the other direction: the
            # breakout engine's startup burst (many symbols advancing
            # indicator state / evaluating signals close together across
            # the 500-symbol universe — largely a startup-transient effect,
            # since a fresh restart compares many symbols' indicator state
            # against thresholds in the same instant, unlike organic price
            # movement during real trading) produced QueuePool timeouts —
            # real missed breakout checks for a handful of symbols, though
            # each just self-heals on the next 30s cycle rather than
            # crashing. 8+4=12 leaves 3 connections of headroom under
            # Supabase's 15 hard cap while giving the startup burst enough
            # room that timeouts became rare rather than eliminated
            # outright — a deliberate tradeoff given the alternative
            # (matching the old 15-connection ceiling) reproduces the
            # actual outage this is meant to prevent. pool_timeout raised
            # to 10s to match — 5s was tuned for the old, larger pool.
            pool_size=8,
            max_overflow=4,
            connect_args=connect_args,
        )
        logger.info("Database engine created")
    return _engine


def _get_session_factory():
    """Lazily create the session factory on first use."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    factory = _get_session_factory()
    async with factory() as session:
        yield session


class _SessionLocalProxy:
    """Proxy so ``async with SessionLocal() as session:`` works lazily."""

    def __call__(self) -> AsyncSession:
        return _get_session_factory()()


SessionLocal = _SessionLocalProxy()


async def check_db_connectivity() -> bool:
    """``SELECT 1`` against the configured database. True on success.

    Never raises — callers (startup validation, /health/ready) treat any
    failure the same way: DB is not currently reachable.
    """
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database connectivity check failed")
        return False
