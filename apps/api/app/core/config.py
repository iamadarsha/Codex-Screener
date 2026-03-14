from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_config_path = Path(__file__).resolve()
API_ENV_FILE = _config_path.parents[2] / ".env"
# In Docker (/app/app/core/config.py) the path is only 4 levels deep,
# so parents[4] would raise IndexError. Fall back to API_ENV_FILE.
REPO_ENV_FILE = _config_path.parents[4] / ".env" if len(_config_path.parents) > 4 else API_ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ENV_FILE), str(API_ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = (
        "postgresql+asyncpg://breakoutscan:breakoutscan@localhost:5432/breakoutscan"
    )
    redis_url: str = "redis://localhost:6379/0"
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = "http://localhost:8001/auth/upstox/callback"
    upstox_api_version: str = "2.0"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    next_public_api_url: str = "http://localhost:8001"
    next_public_ws_url: str = "ws://localhost:8001"
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""
    indian_api_key: str = ""
    gemini_api_key: str = ""
    gemini_backup_api_key: str = ""
    telegram_bot_token: str = ""
    fcm_server_key: str = ""
    environment: str = "development"
    debug: bool = False
    market_timezone: str = "Asia/Kolkata"
    redis_short_ttl_seconds: int = 300
    redis_indicator_ttl_seconds: int = 600
    redis_instrument_ttl_seconds: int = 86400
    redis_token_ttl_seconds: int = 28800
    redis_oauth_state_ttl_seconds: int = 600
    nse_fallback_silence_seconds: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
