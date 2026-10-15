import sys
from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    conversation_service_url: str = ""
    user_service_url: str = ""
    internal_service_token: str = Field(default="local-development-token-32chars-minimum")
    redis_url: str = ""
    rabbitmq_url: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"
    instance_id: str = "local"
    max_frame_bytes: int = 65536
    max_queue_size: int = 100

    @model_validator(mode="after")
    def production_requirements(self):
        if self.app_env != "production":
            return self
        if not self.jwt_public_key.strip():
            raise ValueError("Production requires JWT_PUBLIC_KEY")
        if not self.redis_url:
            raise ValueError("Production requires REDIS_URL")
        redis_host = urlparse(self.redis_url).hostname
        if redis_host in {None, "localhost", "127.0.0.1"}:
            raise ValueError("Production requires external REDIS_URL")
        if (
            not self.internal_service_token
            or self.internal_service_token == "local-development-token-32chars-minimum"
            or len(self.internal_service_token) < 32
        ):
            raise ValueError("Production requires INTERNAL_SERVICE_TOKEN")
        if not self.conversation_service_url:
            raise ValueError("Production requires CONVERSATION_SERVICE_URL")
        return self


@lru_cache
def settings():
    if "pytest" in sys.modules:
        return Settings(_env_file=None, app_env="test")
    return Settings()


class ProtocolError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
