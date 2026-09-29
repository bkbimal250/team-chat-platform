from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import Settings


def test_cors_origins_are_read_from_comma_separated_environment_setting():
    configured = Settings(CORS_ALLOWED_ORIGINS="https://admin.example.com, https://app.example.com")

    assert configured.cors_origins == ["https://admin.example.com", "https://app.example.com"]


def test_cors_wildcard_is_not_enabled_with_credentialed_cors():
    configured = Settings(CORS_ALLOWED_ORIGINS="https://admin.example.com,*")

    assert configured.cors_origins == []


def test_only_configured_origins_receive_credentialed_cors_headers():
    configured = Settings(CORS_ALLOWED_ORIGINS="https://admin.example.com")
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
    )
    client = TestClient(app)

    allowed = client.options(
        "/", headers={"Origin": "https://admin.example.com", "Access-Control-Request-Method": "GET"}
    )
    blocked = client.options(
        "/",
        headers={
            "Origin": "https://unconfigured.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "https://admin.example.com"
    assert "access-control-allow-origin" not in blocked.headers


def test_empty_cors_configuration_is_safe():
    assert Settings(CORS_ALLOWED_ORIGINS=" , ").cors_origins == []
