from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.errors import DomainError


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
            response.raise_for_status()
            result = response.text.strip().lower()
            if not result or any(marker in result for marker in ("error", "invalid", "failed")):
                raise ValueError("unaccepted response")
        except (httpx.HTTPError, ValueError) as exc:
            raise DomainError(
                "OTP_DELIVERY_FAILED",
                "The verification code could not be delivered. Please try again later.",
                503,
            ) from exc
