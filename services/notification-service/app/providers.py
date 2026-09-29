import asyncio
import json
from dataclasses import dataclass
from typing import Protocol

import firebase_admin
from firebase_admin import credentials, messaging


@dataclass
class ProviderResult:
    success: bool
    provider_message_id: str | None = None
    error_code: str | None = None
    retryable: bool = False
    token_invalid: bool = False


class PushProvider(Protocol):
    async def send(self, token, payload) -> ProviderResult: ...


class ProviderRouter:
    """Routes persisted delivery providers to concrete integrations."""

    def __init__(self, providers: dict[str, PushProvider]):
        self.providers = {name.upper(): provider for name, provider in providers.items()}

    async def send(self, provider_name, token, payload):
        provider = self.providers.get(provider_name.upper())
        if provider is None:
            return ProviderResult(False, error_code="unsupported provider")
        return await provider.send(token, payload)


class FirebaseFCMProvider:
    """Firebase Admin boundary. Credentials are injected at runtime, never from image files."""

    def __init__(self, credentials_json: str):
        try:
            certificate = credentials.Certificate(json.loads(credentials_json))
            self.app = firebase_admin.initialize_app(certificate)
        except Exception as exc:
            raise RuntimeError("Firebase credentials are invalid") from exc

    async def send(self, token, payload) -> ProviderResult:
        notification = payload.get("notification", {})
        message = messaging.Message(
            token=token.token,
            notification=messaging.Notification(
                title=notification.get("title"), body=notification.get("body")
            )
            if notification
            else None,
            data={str(key): str(value) for key, value in payload.get("data", {}).items()},
        )
        try:
            message_id = await asyncio.to_thread(messaging.send, message, app=self.app)
            return ProviderResult(True, provider_message_id=message_id)
        except messaging.UnregisteredError:
            return ProviderResult(False, error_code="unregistered token", token_invalid=True)
        except messaging.SenderIdMismatchError:
            return ProviderResult(False, error_code="invalid token", token_invalid=True)
        except messaging.QuotaExceededError:
            return ProviderResult(False, error_code="provider quota exceeded", retryable=True)
        except messaging.UnavailableError:
            return ProviderResult(False, error_code="provider unavailable", retryable=True)
        except firebase_admin.exceptions.FirebaseError:
            return ProviderResult(False, error_code="provider delivery failed")


class FakePushProvider:
    def __init__(self, result: ProviderResult | None = None):
        self.result, self.sent = result or ProviderResult(True, "push-1"), []

    async def send(self, token, payload):
        self.sent.append((token.id, payload))
        return self.result
