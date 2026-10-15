import pytest
from pydantic import ValidationError

from app.core import Settings


@pytest.mark.parametrize(
    "overrides",
    [
        {"database_url": ""},
        {"database_url": "sqlite+aiosqlite:///local.db"},
        {"database_url": "postgresql+asyncpg://user:pass@localhost/messages"},
        {"rabbitmq_url": ""},
        {"rabbitmq_url": "amqp://guest:guest@broker.internal/%2F"},
        {"internal_service_token": ""},
        {"jwt_public_key": ""},
    ],
)
def test_production_rejects_missing_or_unsafe_dependencies(overrides):
    values = {
        "app_env": "production",
        "database_url": "postgresql+asyncpg://service:secret@rds.internal/messages",
        "rabbitmq_url": "amqp://service:secret@mq.internal/%2F",
        "internal_service_token": "strong-test-only-token-32-characters-min",
        "jwt_public_key": "production-public-key",
    }
    values.update(overrides)
    with pytest.raises(ValidationError):
        Settings(**values)


def test_production_accepts_external_injected_dependencies():
    configured = Settings(
        app_env="production",
        database_url="postgresql+asyncpg://service:secret@rds.internal/messages",
        rabbitmq_url="amqp://service:secret@mq.internal/%2F",
        internal_service_token="strong-test-only-token-32-characters-minimum",
        jwt_public_key="production-public-key",
    )
    assert configured.app_env == "production"


def test_development_defaults_remain_available(monkeypatch):
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    assert Settings(_env_file=None).rabbitmq_url.startswith("amqp://guest:guest@localhost")
