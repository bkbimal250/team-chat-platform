from typing import Literal, Optional

from pydantic import AnyUrl, Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # General
    APP_ENV: Literal["development", "staging", "production"] = Field("development", env="APP_ENV")
    SERVICE_NAME: str = Field("identity-service", env="SERVICE_NAME")

    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: RedisDsn = Field(..., env="REDIS_URL")

    # RabbitMQ
    RABBITMQ_URL: AnyUrl = Field(..., env="RABBITMQ_URL")

    # JWT / Token settings
    ACCESS_TOKEN_TTL: int = Field(900, env="ACCESS_TOKEN_TTL")  # seconds (15m)
    REFRESH_TOKEN_TTL: int = Field(2592000, env="REFRESH_TOKEN_TTL")  # seconds (30d)
    ACCESS_TOKEN_PRIVATE_KEY: str = Field(..., env="ACCESS_TOKEN_PRIVATE_KEY")
    ACCESS_TOKEN_PUBLIC_KEY: str = Field(..., env="ACCESS_TOKEN_PUBLIC_KEY")
    ACCESS_TOKEN_ALG: str = Field("RS256", env="ACCESS_TOKEN_ALG")

    # OTP settings
    OTP_TTL: int = Field(300, env="OTP_TTL")  # seconds (5m)
    OTP_MAX_ATTEMPTS: int = Field(5, env="OTP_MAX_ATTEMPTS")
    OTP_RESEND_COOLDOWN: int = Field(60, env="OTP_RESEND_COOLDOWN")  # seconds
    OTP_PROVIDER: Literal["dev", "sms"] = Field("dev", env="OTP_PROVIDER")

    # QR login settings
    QR_CHALLENGE_TTL: int = Field(120, env="QR_CHALLENGE_TTL")  # seconds (2m)
    QR_DEEP_LINK_BASE: AnyUrl = Field(
        "https://app.example.com/link-device", env="QR_DEEP_LINK_BASE"
    )

    # Registration policy
    REGISTRATION_POLICY: Literal["invite_only", "open", "domain_controlled"] = Field(
        "invite_only", env="REGISTRATION_POLICY"
    )

    # Internal service auth (simple token for now)
    SERVICE_AUTH_TOKEN: str = Field(..., env="SERVICE_AUTH_TOKEN")
    ORGANIZATION_SERVICE_URL: AnyUrl = Field(
        "http://organization-service:8000", env="ORGANIZATION_SERVICE_URL"
    )

    # Rate limits (format: "count/period_seconds")
    RATE_LIMIT_OTP_REQUEST: str = Field("5/600", env="RATE_LIMIT_OTP_REQUEST")
    RATE_LIMIT_OTP_VERIFY: str = Field("10/600", env="RATE_LIMIT_OTP_VERIFY")
    RATE_LIMIT_QR_CREATE: str = Field("5/60", env="RATE_LIMIT_QR_CREATE")
    RATE_LIMIT_QR_AUTHORIZE: str = Field("10/60", env="RATE_LIMIT_QR_AUTHORIZE")

    # Trusted proxy handling (comma separated list of CIDR strings)
    TRUSTED_PROXIES: Optional[str] = Field(None, env="TRUSTED_PROXIES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # The API layer uses lower-case names while the original settings contract
    # uses environment-style names. Keep a single source of truth during the
    # transition instead of maintaining two divergent configuration objects.
    @property
    def app_env(self) -> str:
        return self.APP_ENV

    @property
    def redis_url(self) -> str:
        return str(self.REDIS_URL)

    @property
    def redis_max_connections(self) -> int:
        return 10

    @property
    def cors_origins(self) -> list[str]:
        return []

    @property
    def access_token_ttl_seconds(self) -> int:
        return self.ACCESS_TOKEN_TTL

    @property
    def refresh_token_ttl_seconds(self) -> int:
        return self.REFRESH_TOKEN_TTL

    @property
    def otp_ttl_seconds(self) -> int:
        return self.OTP_TTL

    @property
    def otp_resend_cooldown_seconds(self) -> int:
        return self.OTP_RESEND_COOLDOWN

    @property
    def qr_challenge_ttl_seconds(self) -> int:
        return self.QR_CHALLENGE_TTL

    @property
    def development_otp_enabled(self) -> bool:
        return self.OTP_PROVIDER == "dev"

    @property
    def internal_service_token(self) -> str:
        return self.SERVICE_AUTH_TOKEN

    @property
    def organization_service_url(self) -> str:
        return str(self.ORGANIZATION_SERVICE_URL).rstrip("/")

    @property
    def rabbitmq_url(self) -> str:
        return str(self.RABBITMQ_URL)

    @property
    def registration_policy(self) -> str:
        return self.REGISTRATION_POLICY.upper()


# Export a singleton for import elsewhere
settings = Settings()


def get_settings() -> Settings:
    """Return the process-wide application settings instance.

    API modules depend on this accessor so configuration is loaded once and
    remains consistent across dependency injection and background workers.
    """

    return settings
