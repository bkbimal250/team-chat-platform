from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    organization_url: AnyHttpUrl = "http://organization.globalchat.internal:8000"
    identity_url: AnyHttpUrl = "http://identity.globalchat.internal:8001"
    user_url: AnyHttpUrl = "http://user.globalchat.internal:8002"
    conversation_url: AnyHttpUrl = "http://conversation.globalchat.internal:8003"
    messaging_url: AnyHttpUrl = "http://messaging.globalchat.internal:8004"
    media_url: AnyHttpUrl = "http://media.globalchat.internal:8005"
    notification_url: AnyHttpUrl = "http://notification.globalchat.internal:8006"
    upstream_connect_timeout_seconds: float = 3.0
    upstream_read_timeout_seconds: float = 15.0
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
        }
