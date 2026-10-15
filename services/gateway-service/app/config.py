from typing import Literal
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    organization_url: AnyHttpUrl = "http://organization.globalchat.internal:8000"
    identity_url: AnyHttpUrl = "http://identity.globalchat.internal:8001"
    user_url: AnyHttpUrl = "http://user.globalchat.internal:8002"
    conversation_url: AnyHttpUrl = "http://conversation.globalchat.internal:8003"
    messaging_url: AnyHttpUrl = "http://messaging.globalchat.internal:8004"
    media_url: AnyHttpUrl = "http://media.globalchat.internal:8005"
    notification_url: AnyHttpUrl = "http://notification.globalchat.internal:8006"
    realtime_url: AnyHttpUrl = "http://realtime.globalchat.internal:8007"
    realtime_public_wss_url: str = "wss://ws.michat.in/api/v1/realtime"
    redis_url: str = ""
    rate_limit_enabled: bool = False
    rate_limit_auth_per_minute: int = 20
    rate_limit_api_per_minute: int = 300
    rate_limit_window_seconds: int = 60
    upstream_connect_timeout_seconds: float = 3.0
    upstream_read_timeout_seconds: float = 15.0
    upstream_idempotent_retries: int = Field(default=1, ge=0, le=2)
    max_request_bytes: int = 2_097_152
    cors_allowed_origins: str = "https://michat.in,https://app.michat.in,https://admin.michat.in"

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def upstreams(self) -> dict[str, str]:
        return {
            "organization": str(self.organization_url).rstrip("/"),
            "identity": str(self.identity_url).rstrip("/"),
            "user": str(self.user_url).rstrip("/"),
            "conversation": str(self.conversation_url).rstrip("/"),
            "messaging": str(self.messaging_url).rstrip("/"),
            "media": str(self.media_url).rstrip("/"),
            "notification": str(self.notification_url).rstrip("/"),
            "realtime": str(self.realtime_url).rstrip("/"),
        }

    @staticmethod
    def _external_http_url(name: str, url: str) -> None:
        host = urlparse(url).hostname
        if not host or host in _LOCAL_HOSTS:
            raise ValueError(f"production requires external {name}")

    @model_validator(mode="after")
    def production_requirements(self):
        if self.app_env != "production":
            return self
        for name, url in self.upstreams.items():
            self._external_http_url(name.upper() + "_URL", url)
        if not self.redis_url.strip():
            raise ValueError("production requires REDIS_URL")
        redis_host = urlparse(self.redis_url).hostname
        if redis_host in _LOCAL_HOSTS or redis_host is None:
            raise ValueError("production requires external REDIS_URL")
        if not self.rate_limit_enabled:
            self.rate_limit_enabled = True
        if not self.realtime_public_wss_url.startswith("wss://"):
            raise ValueError("production requires REALTIME_PUBLIC_WSS_URL with wss:// scheme")
        return self
