from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = (
        "postgresql+asyncpg://messaging:messaging@localhost:5432/teamchat_message_db"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"
    internal_service_token: str = Field(default="local-development-token")

    @model_validator(mode="after")
    def require_external_production_dependencies(self):
        if self.app_env != "production":
            return self
        database = urlparse(self.database_url)
        if (
            not self.database_url
            or database.scheme.startswith("sqlite")
            or database.hostname in {None, "localhost", "127.0.0.1"}
        ):
            raise ValueError("Production requires an external DATABASE_URL")
        rabbit = urlparse(self.rabbitmq_url)
        if not self.rabbitmq_url or rabbit.hostname in {None, "localhost", "127.0.0.1"}:
            raise ValueError("Production requires an external RABBITMQ_URL")
        if rabbit.username == "guest" and rabbit.password == "guest":
            raise ValueError("Production rejects RabbitMQ guest credentials")
        if (
            not self.internal_service_token
            or self.internal_service_token == "local-development-token"
        ):
            raise ValueError("Production requires an external INTERNAL_SERVICE_TOKEN")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
