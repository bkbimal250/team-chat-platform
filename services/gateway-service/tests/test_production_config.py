import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_requires_external_upstreams_and_redis():
    with pytest.raises(ValidationError):
        Settings(app_env="production", redis_url="redis://127.0.0.1:6379/0")


def test_production_accepts_external_configuration():
    settings = Settings(
        app_env="production",
        organization_url="http://organization.internal:8000",
        identity_url="http://identity.internal:8001",
        user_url="http://user.internal:8002",
        conversation_url="http://conversation.internal:8003",
        messaging_url="http://messaging.internal:8004",
        media_url="http://media.internal:8005",
        notification_url="http://notification.internal:8006",
        realtime_url="http://realtime.internal:8007",
        redis_url="redis://redis.internal:6379/0",
        realtime_public_wss_url="wss://ws.michat.in/api/v1/realtime",
    )
    assert settings.rate_limit_enabled is True
