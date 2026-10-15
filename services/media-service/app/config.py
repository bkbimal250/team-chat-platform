import sys
from dataclasses import dataclass, field
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    conversation_api_url: str = "http://conversation.globalchat.internal:8003"
    internal_service_token: str = ""
    database_url: str = "postgresql+asyncpg://localhost/teamchat_media_db"
    media_storage_backend: Literal["fake", "s3", "local"] = "fake"
    local_storage_root: str = ".local-media"
    local_storage_secret: str = ""
    local_storage_base_url: str = "http://127.0.0.1:8005"
    aws_region: str | None = None
    media_s3_bucket: str | None = None
    media_s3_endpoint_url: str | None = None
    jwt_public_key: str = ""
    jwt_algorithm: Literal["RS256"] = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"

    @model_validator(mode="after")
    def validate_storage(self):
        if self.media_storage_backend == "local" and len(self.local_storage_secret) < 32:
            raise ValueError("local storage requires a minimum 32-character signing secret")
        if self.app_env == "production" and self.media_storage_backend != "s3":
            raise ValueError("production requires MEDIA_STORAGE_BACKEND=s3")
        if self.app_env == "production" and not self.jwt_public_key:
            raise ValueError("production requires JWT_PUBLIC_KEY")
        if self.app_env == "production" and (
            not self.internal_service_token or len(self.internal_service_token) < 32
        ):
            raise ValueError("production requires INTERNAL_SERVICE_TOKEN")
        if self.app_env == "production" and not self.conversation_api_url:
            raise ValueError("production requires CONVERSATION_API_URL")
        if self.app_env == "production":
            database = make_url(self.database_url)
            if database.get_backend_name() != "postgresql" or database.host in {
                None,
                "localhost",
                "127.0.0.1",
            }:
                raise ValueError("production requires a non-local PostgreSQL DATABASE_URL")
        if self.media_storage_backend == "s3":
            if not self.aws_region:
                raise ValueError("MEDIA_STORAGE_BACKEND=s3 requires AWS_REGION")
            if not self.media_s3_bucket:
                raise ValueError("MEDIA_STORAGE_BACKEND=s3 requires MEDIA_S3_BUCKET")
        return self


def get_settings() -> MediaSettings:
    if "pytest" in sys.modules:
        return MediaSettings(_env_file=None, app_env="test")
    return MediaSettings()


@dataclass(frozen=True)
class MediaPolicy:
    bucket: str = "team-chat-platform-private"
    upload_ttl_seconds: int = 900
    pending_ttl_seconds: int = 3600
    ready_retention_seconds: int = 7 * 24 * 3600
    max_upload_size_bytes: int = 5 * 1024 * 1024 * 1024
    multipart_threshold_bytes: int = 16 * 1024 * 1024
    multipart_part_size_bytes: int = 16 * 1024 * 1024
    multipart_max_parts: int = 10_000
    multipart_url_batch_limit: int = 25
    allowed: dict[str, set[str]] = field(
        default_factory=lambda: {
            "image": {"image/jpeg", "image/png", "image/webp"},
            "video": {"video/mp4", "video/webm"},
            "audio": {"audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"},
            "voice": {"audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"},
            "document": {"application/pdf"},
        }
    )
    maximum: dict[str, int] = field(
        default_factory=lambda: {
            "image": 10 * 1024 * 1024,
            "video": 5 * 1024 * 1024 * 1024,
            "audio": 5 * 1024 * 1024 * 1024,
            "voice": 16 * 1024 * 1024,
            "document": 5 * 1024 * 1024 * 1024,
        }
    )
