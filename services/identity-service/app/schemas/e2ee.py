import base64
import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_B64 = re.compile(r"^[A-Za-z0-9+/]+=*$")


def _decode_b64(value: str, min_len: int, max_len: int) -> bytes:
    if not _B64.fullmatch(value) or len(value) > max_len * 2:
        raise ValueError("Invalid base64 key material.")
    raw = base64.b64decode(value, validate=True)
    if not (min_len <= len(raw) <= max_len):
        raise ValueError("Invalid key length.")
    return raw


class OneTimePreKeyUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pre_key_id: int = Field(ge=1, le=2_000_000_000)
    public_key: str

    @field_validator("public_key")
    @classmethod
    def key(cls, value: str) -> str:
        _decode_b64(value, 32, 64)
        return value


class DeviceKeysUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registration_id: int = Field(ge=1, le=16383)
    identity_key: str
    signed_pre_key: dict
    kyber_pre_key: dict
    one_time_pre_keys: list[OneTimePreKeyUpload] = Field(default_factory=list, max_length=200)

    @field_validator("identity_key")
    @classmethod
    def identity(cls, value: str) -> str:
        _decode_b64(value, 32, 33)
        return value

    @field_validator("signed_pre_key")
    @classmethod
    def signed(cls, value: dict) -> dict:
        _validate_signed(value)
        return value

    @field_validator("kyber_pre_key")
    @classmethod
    def kyber(cls, value: dict) -> dict:
        _validate_kyber(value)
        return value


def _validate_signed(value: dict) -> None:
    key_id = value.get("key_id")
    public_key = value.get("public_key")
    signature = value.get("signature")
    if not isinstance(key_id, int) or key_id < 1:
        raise ValueError("signed_pre_key.key_id invalid")
    if not isinstance(public_key, str):
        raise ValueError("signed_pre_key.public_key invalid")
    if not isinstance(signature, str):
        raise ValueError("signed_pre_key.signature invalid")
    _decode_b64(public_key, 32, 64)
    _decode_b64(signature, 64, 128)


def _validate_kyber(value: dict) -> None:
    key_id = value.get("key_id")
    public_key = value.get("public_key")
    signature = value.get("signature")
    if not isinstance(key_id, int) or key_id < 1:
        raise ValueError("kyber_pre_key.key_id invalid")
    if not isinstance(public_key, str):
        raise ValueError("kyber_pre_key.public_key invalid")
    if not isinstance(signature, str):
        raise ValueError("kyber_pre_key.signature invalid")
    _decode_b64(public_key, 100, 2048)
    _decode_b64(signature, 64, 128)


class PreKeyReplenishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    one_time_pre_keys: list[OneTimePreKeyUpload] = Field(min_length=1, max_length=200)


class PublicDeviceE2eeResponse(BaseModel):
    device_id: UUID
    platform: str
    device_name: str
    status: str
    registration_id: int | None = None
    key_version: int | None = None
    identity_key_fingerprint: str | None = None
    rotated_at: datetime | None = None


class PreKeyBundleResponse(BaseModel):
    registration_id: int
    device_id: UUID
    identity_id: UUID
    key_version: int
    identity_key: str
    signed_pre_key: dict
    kyber_pre_key: dict
    one_time_pre_key: dict | None = None
