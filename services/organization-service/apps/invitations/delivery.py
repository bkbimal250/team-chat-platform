"""Delivery seam: no paid delivery, secrets in logs or production development links."""

from abc import ABC, abstractmethod
from urllib.parse import urlparse

from django.conf import settings

from common.exceptions import DomainError


class InvitationDeliveryProvider(ABC):
    @abstractmethod
    def deliver(self, token): ...


class DevelopmentInvitationProvider(InvitationDeliveryProvider):
    def deliver(self, token):
        if settings.ENVIRONMENT not in {"local", "test"}:
            raise DomainError("DELIVERY_UNAVAILABLE", "Invitation delivery is not configured.", 503)
        base = settings.WEB_APP_BASE_URL.rstrip("/")
        parsed = urlparse(base)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise DomainError(
                "DELIVERY_UNAVAILABLE",
                "Development invitations require a local web application URL.",
                503,
            )
        return base + "/join#invite=" + token


def delivery_provider():
    if settings.ENVIRONMENT not in {"local", "test"}:
        raise DomainError("DELIVERY_UNAVAILABLE", "Invitation delivery is not configured.", 503)
    return DevelopmentInvitationProvider()
