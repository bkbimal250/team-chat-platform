from abc import ABC, abstractmethod


class OTPProvider(ABC):
    @abstractmethod
    async def send_otp(self, phone_number: str, code: str) -> None:
        """Send the OTP code to the given phone number."""
        raise NotImplementedError


class DevelopmentOTPProvider(OTPProvider):
    async def send_otp(self, phone_number: str, code: str) -> None:
        # In development we simply log the OTP; never send real SMS.
        # Using structured logging from app.core.logging
        from app.core.logging import logger

        logger.info("[DEV OTP] Sending OTP", extra={"phone_number": phone_number, "code": code})
