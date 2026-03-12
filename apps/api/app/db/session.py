from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# Use SSL for cloud databases (Supabase, etc.), skip for localhost
_connect_args: dict = {}
if "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url:
    _connect_args["ssl"] = "require"

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

