from typing import Literal, Optional

from pydantic import AnyHttpUrl, AnyUrl, Field, PostgresDsn, RedisDsn, model_validator
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
    OTP_PROVIDER: Literal["development", "sms", "vonage_verify"] = Field(
        "development", env="OTP_PROVIDER"
    )
    SMS_PROVIDER: Literal["hilite_http"] | None = Field(None, env="SMS_PROVIDER")
    SMS_API_BASE_URL: AnyHttpUrl | None = Field(None, env="SMS_API_BASE_URL")
    SMS_USERNAME: str | None = Field(None, env="SMS_USERNAME")
    SMS_API_KEY: str | None = Field(None, env="SMS_API_KEY")
    SMS_ROUTE: str | None = Field(None, env="SMS_ROUTE")
    SMS_SENDER_ID: str | None = Field(None, env="SMS_SENDER_ID")
    SMS_TEMPLATE_ID: str | None = Field(None, env="SMS_TEMPLATE_ID")
    SMS_MESSAGE_TEMPLATE: str | None = Field(None, env="SMS_MESSAGE_TEMPLATE")
    SMS_TIMEOUT_SECONDS: float = Field(5.0, gt=0, le=30, env="SMS_TIMEOUT_SECONDS")
    VONAGE_API_KEY: str | None = Field(None, env="VONAGE_API_KEY")
    VONAGE_API_SECRET: str | None = Field(None, env="VONAGE_API_SECRET")
    VONAGE_BRAND: str | None = Field(None, min_length=1, max_length=18, env="VONAGE_BRAND")
    VONAGE_VERIFY_BASE_URL: AnyHttpUrl = Field(
        "https://api.nexmo.com", env="VONAGE_VERIFY_BASE_URL"
    )
    VONAGE_TIMEOUT_SECONDS: float = Field(5.0, gt=0, le=30, env="VONAGE_TIMEOUT_SECONDS")

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
    CORS_ALLOWED_ORIGINS: str = Field("", env="CORS_ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @model_validator(mode="after")
    def validate_otp_provider(self):
        if self.APP_ENV == "production" and self.OTP_PROVIDER not in {"sms", "vonage_verify"}:
            raise ValueError("production requires an external OTP provider")
        if self.OTP_PROVIDER == "sms":
            required = {
                "SMS_PROVIDER": self.SMS_PROVIDER,
                "SMS_API_BASE_URL": self.SMS_API_BASE_URL,
                "SMS_USERNAME": self.SMS_USERNAME,
                "SMS_API_KEY": self.SMS_API_KEY,
                "SMS_ROUTE": self.SMS_ROUTE,
                "SMS_SENDER_ID": self.SMS_SENDER_ID,
                "SMS_TEMPLATE_ID": self.SMS_TEMPLATE_ID,
                "SMS_MESSAGE_TEMPLATE": self.SMS_MESSAGE_TEMPLATE,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"SMS delivery configuration missing: {', '.join(missing)}")
        if self.OTP_PROVIDER == "vonage_verify":
            required = {
                "VONAGE_API_KEY": self.VONAGE_API_KEY,
                "VONAGE_API_SECRET": self.VONAGE_API_SECRET,
                "VONAGE_BRAND": self.VONAGE_BRAND,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"Vonage Verify configuration missing: {', '.join(missing)}")
        return self

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
        origins = [
            origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
        ]
        return [] if "*" in origins else origins

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
    def otp_max_attempts(self) -> int:
        return self.OTP_MAX_ATTEMPTS

    @property
    def otp_resend_cooldown_seconds(self) -> int:
        return self.OTP_RESEND_COOLDOWN

    @property
    def qr_challenge_ttl_seconds(self) -> int:
        return self.QR_CHALLENGE_TTL

    @property
    def development_otp_enabled(self) -> bool:
        return self.OTP_PROVIDER == "development"

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
