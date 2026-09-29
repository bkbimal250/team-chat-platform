from dataclasses import dataclass, field
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    media_storage_backend: Literal["fake", "s3"] = "fake"
    aws_region: str | None = None
    media_s3_bucket: str | None = None
    media_s3_endpoint_url: str | None = None
    jwt_public_key: str = ""
    jwt_algorithm: Literal["RS256"] = "RS256"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "team-chat-platform"

    @model_validator(mode="after")
    def validate_storage(self):
        if self.app_env == "production" and self.media_storage_backend != "s3":
            raise ValueError("production requires MEDIA_STORAGE_BACKEND=s3")
        if self.app_env == "production" and not self.jwt_public_key:
            raise ValueError("production requires JWT_PUBLIC_KEY")
        if self.media_storage_backend == "s3":
            if not self.aws_region:
                raise ValueError("MEDIA_STORAGE_BACKEND=s3 requires AWS_REGION")
            if not self.media_s3_bucket:
                raise ValueError("MEDIA_STORAGE_BACKEND=s3 requires MEDIA_S3_BUCKET")
        return self


def get_settings() -> MediaSettings:
    return MediaSettings()


@dataclass(frozen=True)
class MediaPolicy:
    bucket: str = "team-chat-platform-private"
    upload_ttl_seconds: int = 900
    pending_ttl_seconds: int = 3600
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
            "document": {"application/pdf"},
        }
    )
    maximum: dict[str, int] = field(
        default_factory=lambda: {
            "image": 10 * 1024 * 1024,
            "video": 5 * 1024 * 1024 * 1024,
            "audio": 5 * 1024 * 1024 * 1024,
            "document": 5 * 1024 * 1024 * 1024,
        }
    )
