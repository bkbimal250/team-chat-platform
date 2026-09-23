from typing import Literal

from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    phone_number: str = Field(
        ..., description="Phone number in international format e.g. +919876543210"
    )
    purpose: Literal["LOGIN", "REGISTER", "PHONE_VERIFY", "RECOVERY"] = Field(
        ..., description="Purpose of the OTP"
    )


class OTPVerify(BaseModel):
    challenge_id: str = Field(..., description="UUID of the OTP challenge")
    code: str = Field(..., min_length=6, max_length=6, description="6‑digit OTP code")
    device: dict = Field(
        ...,
        description="Device registration info, passed through to device registration after verification",
    )
