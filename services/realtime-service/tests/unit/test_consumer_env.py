import os

import pytest

from app.consumer_runner import _validate_consumer_env


def test_production_consumer_rejects_local_rabbit(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1/")
    with pytest.raises(RuntimeError, match="external RABBITMQ_URL"):
        _validate_consumer_env()


def test_development_consumer_skips_rabbit_validation(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    _validate_consumer_env()
