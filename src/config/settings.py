"""
OmniSLM Configuration Module.

Centralizes all application settings using Pydantic BaseSettings.
Settings are loaded from environment variables and .env files.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "OmniSLM"
    app_version: str = "0.1.0"
    environment: str = "development"  # development | staging | production
    debug: bool = True
    log_level: str = "INFO"

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://omnislm:omnislm@localhost:5432/omnislm"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- Ollama ----
    ollama_base_url: str = "http://localhost:11434"

    # ---- JWT Authentication ----
    jwt_secret_key: str = "change-this-to-a-random-64-char-string-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ---- API Keys ----
    api_key_prefix: str = "omnislm_sk_"

    # ---- Rate Limiting ----
    rate_limit_per_minute: int = 60

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
