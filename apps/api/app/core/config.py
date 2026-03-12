from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = (
        "postgresql+asyncpg://breakoutscan:breakoutscan@localhost:5432/breakoutscan"
    )
    redis_url: str = "redis://localhost:6379/0"
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = "http://localhost:8000/auth/callback"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    next_public_api_url: str = "http://localhost:8000"
    next_public_ws_url: str = "ws://localhost:8000"
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""
    indian_api_key: str = ""
    telegram_bot_token: str = ""
    fcm_server_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

