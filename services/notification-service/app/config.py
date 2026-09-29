from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "postgresql+asyncpg://localhost/teamchat_notification_db"
    rabbitmq_url: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"
    push_provider: Literal["fake", "fcm"] = "fake"
    firebase_credentials_json: str | None = None
    delivery_poll_seconds: float = 1.0

    @model_validator(mode="after")
    def production_requirements(self):
        if self.app_env == "production":
            if not self.jwt_public_key:
                raise ValueError("production requires JWT_PUBLIC_KEY")
            if self.push_provider != "fcm":
                raise ValueError("production requires PUSH_PROVIDER=fcm")
        if self.push_provider == "fcm" and not self.firebase_credentials_json:
            raise ValueError("PUSH_PROVIDER=fcm requires FIREBASE_CREDENTIALS_JSON")
        return self


def get_settings() -> NotificationSettings:
    return NotificationSettings()
