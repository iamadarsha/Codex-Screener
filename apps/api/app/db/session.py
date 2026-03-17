from __future__ import annotations

import logging
from collections.abc import AsyncIterator

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
            pool_timeout=5,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
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
