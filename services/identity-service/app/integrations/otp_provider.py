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
    async def send_otp(self, phone_number: str, code: str) -> str | None:
        """Send the OTP code to the given phone number."""
        raise NotImplementedError

    async def verify_otp(self, request_id: str, code: str) -> None:
        """Verify an externally managed OTP challenge when supported."""
        return None


class DevelopmentOTPProvider(OTPProvider):
    async def send_otp(self, phone_number: str, code: str) -> str | None:
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


@dataclass(frozen=True)
class VonageVerifyOTPProvider(OTPProvider):
    api_key: str
    api_secret: str
    brand: str
    base_url: str
    timeout_seconds: float

    async def send_otp(self, phone_number: str, code: str) -> str | None:
        del code
        result = await self._post(
            "/verify/json",
            {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "number": phone_number.removeprefix("+"),
                "brand": self.brand,
                "code_length": "6",
            },
            operation="request",
        )
        request_id = result.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            self._raise_provider_error("provider_rejection", 503)
        return request_id

    async def verify_otp(self, request_id: str, code: str) -> None:
        await self._post(
            "/verify/check/json",
            {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "request_id": request_id,
                "code": code,
            },
            operation="check",
        )

    async def _post(self, path: str, data: dict[str, str], *, operation: str) -> dict[str, object]:
        started = time.monotonic()
        provider_host = urlparse(self.base_url).hostname or "unknown"
        logger.info(
            "vonage_verify_request_started",
            extra={
                "provider_host": provider_host,
                "provider_category": operation,
                "duration_ms": 0,
            },
        )
        timeout = httpx.Timeout(self.timeout_seconds, connect=min(self.timeout_seconds, 3.0))
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url.rstrip('/')}{path}", data=data)
            logger.info(
                "vonage_verify_response_received",
                extra={
                    "provider_host": provider_host,
                    "provider_status": response.status_code,
                    "provider_category": operation,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                },
            )
            response.raise_for_status()
            result = response.json()
        except httpx.TimeoutException as exc:
            self._log_failure(provider_host, "timeout", started)
            raise DomainError("OTP_DELIVERY_FAILED", "Verification is unavailable.", 503) from exc
        except httpx.ConnectError as exc:
            self._log_failure(provider_host, "network_failure", started)
            raise DomainError("OTP_DELIVERY_FAILED", "Verification is unavailable.", 503) from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._log_failure(provider_host, "http_protocol_failure", started)
            raise DomainError("OTP_DELIVERY_FAILED", "Verification is unavailable.", 503) from exc
        if not isinstance(result, dict):
            self._raise_provider_error("provider_rejection", 503)
        status = str(result.get("status", ""))
        if status != "0":
            category, error_code, status_code = self._category(status, operation)
            logger.warning(
                "vonage_verify_rejected",
                extra={
                    "provider_host": provider_host,
                    "provider_status": response.status_code,
                    "provider_category": category,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                },
            )
            raise DomainError(error_code, "Verification could not be completed.", status_code)
        return result

    @staticmethod
    def _category(status: str, operation: str) -> tuple[str, str, int]:
        if status in {"1", "9", "10", "17"}:
            return "rate_limit", "OTP_TOO_MANY_ATTEMPTS", 429
        if status in {"3", "4"}:
            return "authentication_failure", "OTP_DELIVERY_FAILED", 503
        if operation == "check" and status == "6":
            return "invalid_code", "OTP_INVALID", 400
        if operation == "check" and status in {"16", "19"}:
            return "expired_code", "OTP_EXPIRED", 400
        return "provider_rejection", "OTP_DELIVERY_FAILED", 503

    @staticmethod
    def _raise_provider_error(category: str, status_code: int) -> None:
        logger.warning("vonage_verify_rejected", extra={"provider_category": category})
        raise DomainError(
            "OTP_DELIVERY_FAILED", "Verification could not be completed.", status_code
        )

    @staticmethod
    def _log_failure(provider_host: str, category: str, started: float) -> None:
        logger.warning(
            "vonage_verify_failed",
            extra={
                "provider_host": provider_host,
                "provider_category": category,
                "duration_ms": round((time.monotonic() - started) * 1000),
            },
        )
