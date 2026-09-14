"""Settings must refuse to construct with an unsafe production DB config.

Caught live (2026-09-14): DATABASE_URL was never set in production, so the
guarded `localhost:5432` dev default silently took over — every candle
persistence write failed forever. This is the regression test for the fix.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings


def test_production_with_localhost_db_raises():
    with pytest.raises(Exception, match="localhost"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://breakoutscan:breakoutscan@localhost:5432/breakoutscan",
        )


def test_production_with_loopback_ip_db_raises():
    with pytest.raises(Exception, match="127.0.0.1"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://x:y@127.0.0.1:5432/breakoutscan",
        )


def test_production_with_empty_db_raises():
    with pytest.raises(Exception, match="DATABASE_URL is empty"):
        Settings(environment="production", database_url="")


def test_production_with_real_db_url_is_accepted():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://postgres.proj:pw@aws-0-ap-south-1.pooler.supabase.com:5432/postgres",
    )
    assert settings.environment == "production"


def test_development_allows_localhost_db():
    settings = Settings(
        environment="development",
        database_url="postgresql+asyncpg://breakoutscan:breakoutscan@localhost:5432/breakoutscan",
    )
    assert "localhost" in settings.database_url
