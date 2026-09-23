from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import DevicePlatform


class DeviceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    installation_id: str = Field(min_length=16, max_length=256)
    platform: DevicePlatform
    device_name: str = Field(min_length=1, max_length=200)
    device_model: str | None = Field(None, max_length=200)
    os_version: str | None = Field(None, max_length=100)
    app_version: str | None = Field(None, max_length=100)


class OTPRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_number: str = Field(max_length=64)
    purpose: str = Field(pattern="^(LOGIN|REGISTER|PHONE_VERIFY|RECOVERY)$")


class OTPRequestResponse(BaseModel):
    challenge_id: UUID | None = None
    message: str = "If eligible, a verification code has been sent."
    development_code: str | None = None


class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: UUID
    code: str = Field(pattern="^\d{6}$")
    device: DeviceInput
    organization_id: UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    session_id: UUID
    device_id: UUID
    organization_id: UUID
    member_id: UUID


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=32, max_length=512)


class QRCreateRequest(DeviceInput):
    pass


class QRCreateResponse(BaseModel):
    challenge_id: UUID
    payload: str
    expires_at: datetime


class QRAuthorizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    secret: str = Field(min_length=32, max_length=512)


class QRConsumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    secret: str = Field(min_length=32, max_length=512)


class ContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: UUID


class RevokeResponse(BaseModel):
    status: str


class DeviceResponse(BaseModel):
    id: UUID
    platform: str
    device_name: str
    device_model: str | None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    is_current: bool


class SessionResponse(BaseModel):
    id: UUID
    device_id: UUID
    platform: str
    device_name: str
    status: str
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    ip_address: str | None
    is_current: bool


class MeResponse(BaseModel):
    identity: dict
    session: dict
    context: dict
