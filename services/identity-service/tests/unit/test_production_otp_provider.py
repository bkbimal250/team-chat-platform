import logging
import re
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.api.v1 import auth
from app.core.config import Settings
from app.core.errors import DomainError
from app.integrations.otp_provider import (
    DevelopmentOTPProvider,
    HiliteSMSOTPProvider,
    VonageVerifyOTPProvider,
)
from app.models.models import OTPStatus
from app.schemas.api import OTPRequestResponse
from app.security.hashing import verify_secret
from app.services.otp_service import OTPService


def settings_values(**overrides):
    values = {
        "APP_ENV": "development",
        "DATABASE_URL": "postgresql+asyncpg://test:test@db/identity_db",
        "REDIS_URL": "redis://redis:6379/0",
        "RABBITMQ_URL": "amqps://user:password@broker:5671",
        "ACCESS_TOKEN_PRIVATE_KEY": "private",
        "ACCESS_TOKEN_PUBLIC_KEY": "public",
        "SERVICE_AUTH_TOKEN": "x" * 32,
        "OTP_PROVIDER": "development",
    }
    values.update(overrides)
    return values


def sms_settings(**overrides):
    return Settings(
        _env_file=None,
        **settings_values(
            OTP_PROVIDER="sms",
            SMS_PROVIDER="hilite_http",
            SMS_API_BASE_URL="https://sms.example.test/send",
            SMS_USERNAME="test-user",
            SMS_API_KEY="secret-api-key",
            SMS_ROUTE="ServiceImplicit",
            SMS_SENDER_ID="GLOBAL",
            SMS_TEMPLATE_ID="otp-template",
            SMS_MESSAGE_TEMPLATE="Your GlobalChat verification code is {otp}.",
            **overrides,
        ),
    )


def test_development_provider_allowed_outside_production():
    settings = Settings(_env_file=None, **settings_values())
    assert settings.development_otp_enabled is True


@pytest.mark.asyncio
async def test_development_provider_executes_in_development():
    assert await DevelopmentOTPProvider().send_otp("+919876543210", "123456") is None


def test_development_provider_rejected_in_production():
    with pytest.raises(ValidationError, match="production requires an external OTP provider"):
        Settings(_env_file=None, **settings_values(APP_ENV="production"))


@pytest.mark.parametrize(
    "missing",
    [
        "SMS_PROVIDER",
        "SMS_API_BASE_URL",
        "SMS_USERNAME",
        "SMS_API_KEY",
        "SMS_ROUTE",
        "SMS_SENDER_ID",
        "SMS_TEMPLATE_ID",
        "SMS_MESSAGE_TEMPLATE",
    ],
)
def test_sms_configuration_fails_closed_when_required_value_missing(missing):
    values = settings_values(APP_ENV="production", OTP_PROVIDER="sms")
    values.update(
        SMS_PROVIDER="hilite_http",
        SMS_API_BASE_URL="https://sms.example.test/send",
        SMS_USERNAME="test-user",
        SMS_API_KEY="secret-api-key",
        SMS_ROUTE="ServiceImplicit",
        SMS_SENDER_ID="GLOBAL",
        SMS_TEMPLATE_ID="otp-template",
        SMS_MESSAGE_TEMPLATE="Your GlobalChat verification code is {otp}.",
    )
    values[missing] = None
    with pytest.raises(ValidationError, match=missing):
        Settings(_env_file=None, **values)


def test_sms_provider_is_selected_without_development_fallback(monkeypatch):
    configured = sms_settings(APP_ENV="production")
    monkeypatch.setattr(auth, "get_settings", lambda: configured)
    service = auth.otp_service(
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis={})))
    )
    assert isinstance(service.provider, HiliteSMSOTPProvider)
    assert not isinstance(service.provider, DevelopmentOTPProvider)


def test_vonage_verify_provider_is_selected_without_fallback(monkeypatch):
    configured = Settings(
        _env_file=None,
        **settings_values(
            APP_ENV="production",
            OTP_PROVIDER="vonage_verify",
            VONAGE_API_KEY="vonage-api-key",
            VONAGE_API_SECRET="vonage-api-secret",
            VONAGE_BRAND="GlobalChat",
        ),
    )
    monkeypatch.setattr(auth, "get_settings", lambda: configured)
    service = auth.otp_service(
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis={})))
    )
    assert isinstance(service.provider, VonageVerifyOTPProvider)


class FakeResponse:
    def __init__(self, accepted=True, error=None, status_code=200):
        self.accepted = accepted
        self.error = error
        self.status_code = status_code

    def raise_for_status(self):
        if self.error:
            raise self.error

    @property
    def text(self):
        return "message-id-123" if self.accepted else "Error: rejected"

    def json(self):
        return {"status": "0", "request_id": "vonage-request-id"}


class FakeClient:
    response = FakeResponse()
    request = None
    timeout = None

    def __init__(self, timeout):
        type(self).timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def get(self, url, *, params):
        type(self).request = (url, params)
        return type(self).response

    async def post(self, url, *, data):
        type(self).request = (url, data)
        return type(self).response


def provider():
    return HiliteSMSOTPProvider(
        "https://sms.example.test/send",
        "test-user",
        "secret-api-key",
        "ServiceImplicit",
        "GLOBAL",
        "otp-template",
        "Your GlobalChat verification code is {otp}.",
        5,
    )


@pytest.mark.asyncio
async def test_http_sms_provider_sends_normalized_destination_and_code(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    await provider().send_otp("+919876543210", "123456")
    _, parameters = FakeClient.request
    assert parameters["mobile"] == "+919876543210"
    assert parameters["message"] == "Your GlobalChat verification code is 123456."
    assert parameters["username"] == "test-user"
    assert parameters["apikey"] == "secret-api-key"
    assert parameters["route"] == "ServiceImplicit"
    assert parameters["TemplateID"] == "otp-template"
    assert parameters["sender"] == "GLOBAL"
    assert FakeClient.timeout.connect == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(error=httpx.TimeoutException("timed out")),
        FakeResponse(accepted=False),
    ],
)
async def test_provider_failures_are_sanitized(monkeypatch, response):
    FakeClient.response = response
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    with pytest.raises(DomainError) as captured:
        await provider().send_otp("+919876543210", "654321")
    message = str(captured.value)
    assert "654321" not in message
    assert "secret-api-key" not in message
    FakeClient.response = FakeResponse()


@pytest.mark.asyncio
async def test_hilite_diagnostics_are_sanitized(monkeypatch, caplog):
    sensitive_phone = "+919876543210"
    sensitive_otp = "654321"
    sensitive_username = "test-user"
    sensitive_key = "secret-api-key"
    FakeClient.response = FakeResponse(accepted=False)
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    with caplog.at_level(logging.INFO), pytest.raises(DomainError):
        await provider().send_otp(sensitive_phone, sensitive_otp)

    log_content = "\n".join(f"{record.getMessage()} {record.__dict__}" for record in caplog.records)
    for value in (sensitive_phone, sensitive_otp, sensitive_username, sensitive_key):
        assert value not in log_content
    assert "hilite_sms_request_started" in log_content
    assert "hilite_sms_response_received" in log_content
    assert "hilite_sms_response_rejected" in log_content
    assert "sms.example.test" in log_content
    assert "provider_error_marker" not in log_content
    assert any(getattr(record, "provider_category", None) == "error" for record in caplog.records)
    FakeClient.response = FakeResponse()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "category"),
    [
        (httpx.TimeoutException("timeout"), "timeout"),
        (httpx.ConnectError("connection failed"), "dns_or_connect_failure"),
        (httpx.RemoteProtocolError("protocol failed"), "http_protocol_failure"),
    ],
)
async def test_hilite_diagnostics_categorize_transport_failures(
    monkeypatch, caplog, error, category
):
    FakeClient.response = FakeResponse(error=error)
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    with caplog.at_level(logging.INFO), pytest.raises(DomainError):
        await provider().send_otp("+919876543210", "654321")

    assert any(getattr(record, "provider_category", None) == category for record in caplog.records)
    FakeClient.response = FakeResponse()


def vonage_provider():
    return VonageVerifyOTPProvider(
        api_key="vonage-api-key",
        api_secret="vonage-api-secret",
        brand="GlobalChat",
        base_url="https://api.nexmo.com",
        timeout_seconds=5,
    )


@pytest.mark.asyncio
async def test_vonage_verify_request_and_check_do_not_expose_sensitive_values(monkeypatch, caplog):
    sensitive_phone = "+919876543210"
    sensitive_code = "654321"
    FakeClient.response = FakeResponse()
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    with caplog.at_level(logging.INFO):
        request_id = await vonage_provider().send_otp(sensitive_phone, sensitive_code)
        await vonage_provider().verify_otp(request_id, sensitive_code)

    assert request_id == "vonage-request-id"
    request_url, request_data = FakeClient.request
    assert request_url.endswith("/verify/check/json")
    assert request_data["request_id"] == request_id
    log_content = "\n".join(f"{record.getMessage()} {record.__dict__}" for record in caplog.records)
    for value in (sensitive_phone, sensitive_code, "vonage-api-key", "vonage-api-secret"):
        assert value not in log_content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_status", "expected_code"),
    [("3", "OTP_DELIVERY_FAILED"), ("6", "OTP_INVALID"), ("16", "OTP_EXPIRED")],
)
async def test_vonage_verify_categorizes_provider_rejections(
    monkeypatch, provider_status, expected_code
):
    class RejectedResponse(FakeResponse):
        def json(self):
            return {"status": provider_status}

    FakeClient.response = RejectedResponse()
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    with pytest.raises(DomainError) as captured:
        await vonage_provider().verify_otp("vonage-request-id", "654321")
    assert captured.value.code == expected_code
    FakeClient.response = FakeResponse()


@pytest.mark.asyncio
async def test_otp_service_maps_and_checks_external_request_id(monkeypatch):
    configured = sms_settings(APP_ENV="production")
    monkeypatch.setattr("app.services.otp_service.get_settings", lambda: configured)
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)

    class VerifyProvider:
        request_id = "vonage-request-id"
        verified = None

        async def send_otp(self, _phone, _code):
            return self.request_id

        async def verify_otp(self, request_id, code):
            self.verified = (request_id, code)

    provider_instance = VerifyProvider()
    database = RequestDb()
    challenge, _ = await OTPService(provider_instance, AllowingLimiter()).request(
        database, "+919876543210", "LOGIN", "127.0.0.1", "correlation"
    )
    challenge.id = uuid4()
    challenge.status = OTPStatus.PENDING
    challenge.attempt_count = 0
    challenge.max_attempts = configured.otp_max_attempts
    assert challenge.provider_request_id == provider_instance.request_id

    await OTPService(provider_instance, AllowingLimiter()).verify(
        VerifyDb(challenge), challenge.id, "654321", "127.0.0.1", "correlation"
    )
    assert provider_instance.verified == (provider_instance.request_id, "654321")
    assert challenge.status == OTPStatus.VERIFIED


def test_vonage_verify_configuration_fails_closed_without_credentials():
    values = settings_values(APP_ENV="production", OTP_PROVIDER="vonage_verify")
    values.update(VONAGE_API_KEY="key", VONAGE_API_SECRET="secret", VONAGE_BRAND="GlobalChat")
    assert Settings(_env_file=None, **values).OTP_PROVIDER == "vonage_verify"
    values["VONAGE_API_SECRET"] = None
    with pytest.raises(ValidationError, match="VONAGE_API_SECRET"):
        Settings(_env_file=None, **values)


class RecordingProvider:
    def __init__(self):
        self.phone = None
        self.code = None

    async def send_otp(self, phone, code):
        self.phone, self.code = phone, code


class RequestDb:
    def __init__(self):
        self.challenge = None

    def add(self, challenge):
        self.challenge = challenge

    async def flush(self):
        return None


class AllowingLimiter:
    async def hit(self, *_):
        return None

    async def cooldown(self, *_):
        return None


async def done(*_, **__):
    return None


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class VerifyDb:
    def __init__(self, challenge):
        self.challenge = challenge

    async def execute(self, _):
        return Result(self.challenge)


@pytest.mark.asyncio
async def test_otp_service_normalizes_phone_hashes_code_and_hides_production_value(monkeypatch):
    configured = sms_settings(APP_ENV="production")
    monkeypatch.setattr("app.services.otp_service.get_settings", lambda: configured)
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)
    delivery = RecordingProvider()
    database = RequestDb()

    challenge, returned_code = await OTPService(delivery, AllowingLimiter()).request(
        database, "+91 98765 43210", "LOGIN", "127.0.0.1", "correlation"
    )

    assert delivery.phone == "+919876543210"
    assert re.fullmatch(r"\d{6}", delivery.code)
    assert verify_secret(delivery.code, challenge.code_hash)
    assert delivery.code not in challenge.code_hash
    assert returned_code is None


@pytest.mark.asyncio
async def test_provider_failure_does_not_log_or_persist_plaintext(monkeypatch, caplog):
    configured = sms_settings(APP_ENV="production")
    monkeypatch.setattr("app.services.otp_service.get_settings", lambda: configured)
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)

    class Failure:
        code = None

        async def send_otp(self, _phone, code):
            self.code = code
            raise DomainError("OTP_DELIVERY_FAILED", "Delivery unavailable.", 503)

    delivery = Failure()
    database = RequestDb()
    with caplog.at_level(logging.DEBUG), pytest.raises(DomainError):
        await OTPService(delivery, AllowingLimiter()).request(
            database, "+919876543210", "LOGIN", "127.0.0.1", "correlation"
        )

    assert delivery.code not in caplog.text
    assert delivery.code not in database.challenge.code_hash
    assert database.challenge.verified_at is None


@pytest.mark.asyncio
async def test_resend_cooldown_prevents_delivery(monkeypatch):
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)
    delivery = RecordingProvider()

    class CooldownLimiter(AllowingLimiter):
        async def cooldown(self, *_):
            raise DomainError("OTP_COOLDOWN", "Please wait before requesting another code.", 429)

    with pytest.raises(DomainError, match="OTP_COOLDOWN"):
        await OTPService(delivery, CooldownLimiter()).request(
            RequestDb(), "+919876543210", "LOGIN", "127.0.0.1", "correlation"
        )
    assert delivery.code is None


@pytest.mark.asyncio
async def test_rate_limit_prevents_delivery(monkeypatch):
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)
    delivery = RecordingProvider()

    class Limited(AllowingLimiter):
        async def hit(self, *_):
            raise DomainError("RATE_LIMITED", "Too many requests.", 429)

    with pytest.raises(DomainError, match="RATE_LIMITED"):
        await OTPService(delivery, Limited()).request(
            RequestDb(), "+919876543210", "LOGIN", "127.0.0.1", "correlation"
        )
    assert delivery.code is None


@pytest.mark.asyncio
async def test_expired_otp_is_rejected(monkeypatch):
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)
    challenge = SimpleNamespace(
        id=uuid4(),
        status=OTPStatus.PENDING,
        attempt_count=0,
        max_attempts=5,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        code_hash="unused",
    )
    with pytest.raises(DomainError, match="OTP_EXPIRED"):
        await OTPService(None, AllowingLimiter()).verify(
            VerifyDb(challenge), challenge.id, "123456", "127.0.0.1", "correlation"
        )
    assert challenge.status == OTPStatus.EXPIRED


@pytest.mark.asyncio
async def test_successful_otp_is_single_use(monkeypatch):
    monkeypatch.setattr("app.services.otp_service.audit_and_event", done)
    from app.security.hashing import hash_secret

    challenge = SimpleNamespace(
        id=uuid4(),
        status=OTPStatus.PENDING,
        attempt_count=0,
        max_attempts=5,
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
        code_hash=hash_secret("123456"),
        verified_at=None,
    )
    service = OTPService(None, AllowingLimiter())
    await service.verify(VerifyDb(challenge), challenge.id, "123456", "127.0.0.1", "correlation")
    assert challenge.status == OTPStatus.VERIFIED
    with pytest.raises(DomainError, match="OTP_REPLAYED"):
        await service.verify(
            VerifyDb(challenge), challenge.id, "123456", "127.0.0.1", "correlation"
        )


def test_production_otp_response_contains_no_plaintext_code():
    response = OTPRequestResponse(challenge_id=uuid4(), development_code=None)
    assert response.development_code is None
    assert "123456" not in response.model_dump_json()
