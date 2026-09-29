from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: UUID
    filename: str = Field(min_length=1, max_length=512)
    mime_type: str
    size_bytes: int = Field(gt=0)
    media_type: str
    checksum_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class MultipartPartsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    part_numbers: list[int] = Field(min_length=1, max_length=25)


class MultipartCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parts: list[dict] = Field(min_length=1, max_length=10_000)
