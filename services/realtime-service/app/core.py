from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    redis_url: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"
    instance_id: str = "local"
    max_frame_bytes: int = 65536
    max_queue_size: int = 100


@lru_cache
def settings():
    return Settings()


class ProtocolError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
