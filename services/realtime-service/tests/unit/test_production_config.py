import pytest
from pydantic import ValidationError

from app.core import Settings


def test_production_requires_external_dependencies():
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_public_key="key",
            redis_url="redis://127.0.0.1:6379/0",
            internal_service_token="local-development-token-32chars-minimum",
            conversation_service_url="http://conversation:8003",
        )


def test_production_accepts_valid_configuration():
    settings = Settings(
        app_env="production",
        jwt_public_key="production-public-key",
        redis_url="redis://redis.internal:6379/0",
        rabbitmq_url="amqp://service:secret@rabbit.internal:5672/%2F",
        internal_service_token="strong-test-only-token-32-characters-min",
        conversation_service_url="http://conversation:8003",
    )
    assert settings.app_env == "production"
