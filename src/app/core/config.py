"""
Application configuration using Pydantic Settings.

All environment variables are managed here. Access via:
    from core.config import settings
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Timstapaper"
    debug: bool = False
    root_path: str = "/"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # Database
    database_path: str = "/data/timstapaper.db"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to avoid reading environment variables on every access.
    """
    return Settings()


settings = get_settings()
