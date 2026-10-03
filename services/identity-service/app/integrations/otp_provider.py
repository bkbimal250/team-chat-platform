import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.errors import DomainError

logger = logging.getLogger(__name__)


class OTPProvider(ABC):
    @abstractmethod
    async def send_otp(self, phone_number: str, code: str) -> None:
        """Send the OTP code to the given phone number."""
        raise NotImplementedError


class DevelopmentOTPProvider(OTPProvider):
    async def send_otp(self, phone_number: str, code: str) -> None:
        return None


@dataclass(frozen=True)
class HiliteSMSOTPProvider(OTPProvider):
    base_url: str
    username: str
    api_key: str
    route: str
    sender_id: str
    template_id: str
    message_template: str
    timeout_seconds: float

    async def send_otp(self, phone_number: str, code: str) -> None:
        started = time.monotonic()
        provider_host = urlparse(self.base_url).hostname or "unknown"
        logger.info(
            "hilite_sms_request_started",
            extra={"provider_host": provider_host, "duration_ms": 0},
        )
        message = self.message_template.replace("{otp}", code)
        parameters = {
            "username": self.username,
            "apikey": self.api_key,
            "apirequest": "Text",
            "route": self.route,
            "TemplateID": self.template_id,
            "sender": self.sender_id,
            "mobile": phone_number,
            "message": message,
        }
        timeout = httpx.Timeout(self.timeout_seconds, connect=min(self.timeout_seconds, 3.0))
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=parameters,
                )
            logger.info(
                "hilite_sms_response_received",
                extra={
                    "provider_host": provider_host,
                    "provider_status": response.status_code,
                    "duration_ms": self._elapsed_milliseconds(started),
                },
            )
            response.raise_for_status()
            result = response.text.strip().lower()
            if not result or any(marker in result for marker in ("error", "invalid", "failed")):
                logger.warning(
                    "hilite_sms_response_rejected",
                    extra={
                        "provider_host": provider_host,
                        "provider_status": response.status_code,
                        "provider_category": self._response_category(result),
                        "duration_ms": self._elapsed_milliseconds(started),
                    },
                )
                raise ValueError("unaccepted response")
            logger.info(
                "hilite_sms_response_accepted",
                extra={
                    "provider_host": provider_host,
                    "provider_status": response.status_code,
                    "provider_category": "accepted",
                    "duration_ms": self._elapsed_milliseconds(started),
                },
            )
        except httpx.TimeoutException as exc:
            self._log_failure(provider_host, "timeout", started)
            raise self._delivery_error() from exc
        except httpx.ConnectError as exc:
            self._log_failure(provider_host, "dns_or_connect_failure", started)
            raise self._delivery_error() from exc
        except httpx.ProtocolError as exc:
            self._log_failure(provider_host, "http_protocol_failure", started)
            raise self._delivery_error() from exc
        except httpx.HTTPStatusError as exc:
            self._log_failure(
                provider_host,
                "http_status_failure",
                started,
                provider_status=exc.response.status_code,
            )
            raise self._delivery_error() from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._log_failure(provider_host, "provider_request_failure", started)
            raise self._delivery_error() from exc

    @staticmethod
    def _elapsed_milliseconds(started: float) -> int:
        return round((time.monotonic() - started) * 1000)

    @staticmethod
    def _response_category(result: str) -> str:
        if not result:
            return "empty"
        if "invalid" in result:
            return "invalid"
        if "failed" in result:
            return "failed"
        return "error"

    def _log_failure(
        self,
        provider_host: str,
        category: str,
        started: float,
        *,
        provider_status: int | None = None,
    ) -> None:
        logger.warning(
            "hilite_sms_delivery_failed",
            extra={
                "provider_host": provider_host,
                "provider_status": provider_status,
                "provider_category": category,
                "duration_ms": self._elapsed_milliseconds(started),
            },
        )

    @staticmethod
    def _delivery_error() -> DomainError:
        return DomainError(
            "OTP_DELIVERY_FAILED",
            "The verification code could not be delivered. Please try again later.",
            503,
        )
