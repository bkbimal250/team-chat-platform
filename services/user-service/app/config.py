import os
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: Literal["development", "staging", "production"] = "development"
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn = "redis://127.0.0.1:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "user.events"
    RABBITMQ_PREFETCH_COUNT: int = 20
    OUTBOX_BATCH_SIZE: int = 50
    OUTBOX_POLL_SECONDS: float = 1.0
    MEDIA_SERVICE_URL: str = "http://media-service:8005"
    IDENTITY_SERVICE_URL: str = "http://identity-service:8001"
    INTERNAL_SERVICE_TOKEN: str = Field(min_length=1, repr=False)
    IDENTITY_JWT_PUBLIC_KEY: str = Field(min_length=1, repr=False)
    IDENTITY_JWT_ALGORITHM: str = "RS256"
    IDENTITY_JWT_ISSUER: str = "identity-service"
    WORKSPACE_SEARCH_RATE_LIMIT: int = 30
    WORKSPACE_SEARCH_RATE_WINDOW_SECONDS: int = 60

    @model_validator(mode="after")
    def validate_production(self):
        if self.APP_ENV in {"staging", "production"}:
            if len(self.INTERNAL_SERVICE_TOKEN) < 32:
                raise ValueError("INTERNAL_SERVICE_TOKEN must be at least 32 characters")
            if self.IDENTITY_JWT_PUBLIC_KEY.strip() in {"", "test-key", "replace-with-identity-public-key"}:
                raise ValueError("IDENTITY_JWT_PUBLIC_KEY must be configured")
            parsed = self.DATABASE_URL
            host = parsed.host if hasattr(parsed, "host") else None
            if host in {None, "localhost", "127.0.0.1"}:
                raise ValueError("production requires a non-local PostgreSQL DATABASE_URL")
        return self


def get_settings() -> Settings:
    return Settings()


def reset_settings() -> None:
    """Compatibility hook for tests that reload configuration."""
