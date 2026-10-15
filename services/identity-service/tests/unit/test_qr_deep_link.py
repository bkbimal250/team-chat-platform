from uuid import uuid4

from app.core.config import Settings
from app.services.qr_deep_link import build_qr_challenge_payload


def test_qr_payload_uses_configured_base_and_query_joining():
    base = "https://app.example.com/link-device"
    challenge_id = uuid4()
    secret = "a" * 32
    payload = build_qr_challenge_payload(base, challenge_id, secret)
    assert payload == f"{base}?challenge={challenge_id}.{secret}"


def test_qr_payload_strips_trailing_slash_from_base():
    challenge_id = uuid4()
    secret = "b" * 32
    payload = build_qr_challenge_payload("https://app.example.com/link-device/", challenge_id, secret)
    assert payload.startswith("https://app.example.com/link-device?challenge=")


def test_settings_default_qr_deep_link_base():
    configured = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://test:test@db/identity_db",
        REDIS_URL="redis://redis:6379/0",
        RABBITMQ_URL="amqp://test:test@broker:5672/",
        ACCESS_TOKEN_PRIVATE_KEY="private-key-material",
        ACCESS_TOKEN_PUBLIC_KEY="public-key-material",
        SERVICE_AUTH_TOKEN="x" * 32,
    )
    payload = build_qr_challenge_payload(str(configured.QR_DEEP_LINK_BASE), uuid4(), "c" * 32)
    assert payload.startswith("https://app.example.com/link-device?challenge=")
