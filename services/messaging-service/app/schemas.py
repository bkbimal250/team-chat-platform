from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class E2eeDeviceCiphertext(BaseModel):
    device_id: UUID
    message_type: int = Field(ge=2, le=8)
    ciphertext: str = Field(min_length=1, max_length=512_000)
    registration_id: int | None = Field(default=None, ge=1, le=16383)


class E2eeEnvelopeIn(BaseModel):
    version: int = Field(default=1, ge=1, le=1)
    mode: str = Field(pattern=r"^(direct|group)$")
    distribution_id: str | None = Field(default=None, max_length=64)
    message_type: int = Field(ge=2, le=8)
    ciphertext: str = Field(min_length=1, max_length=512_000)
    device_payloads: list[E2eeDeviceCiphertext] = Field(min_length=1, max_length=256)


class SendMessage(BaseModel):
    client_message_id: UUID
    type: str = "TEXT"
    text: str | None = Field(default=None, min_length=1, max_length=10000)
    media_id: UUID | None = None
    e2ee: E2eeEnvelopeIn | None = None

    @model_validator(mode="after")
    def content(self):
        if self.forward_from_message_id is not None:
            return self
        if self.type == "E2EE":
            if self.text or self.media_id or not self.e2ee:
                raise ValueError("E2EE messages require e2ee envelope only")
            return self
        if self.type == "TEXT":
            if not self.text or not self.text.strip() or self.media_id or self.e2ee:
                raise ValueError("Text content is required without media")
        elif self.type == "SYSTEM":
            return self
        elif self.type not in {"IMAGE", "VIDEO", "AUDIO", "VOICE", "DOCUMENT"} or not self.media_id:
            raise ValueError("A supported media type and media_id are required")
        elif self.e2ee:
            raise ValueError("Plaintext media cannot include e2ee envelope")
        return self

    reply_to_message_id: UUID | None = None
    forward_from_message_id: UUID | None = None
    mentioned_member_ids: list[UUID] | None = None


class BroadcastListIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class BroadcastRecipientIn(BaseModel):
    contact_id: UUID


class EditMessage(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=10000)
    e2ee: E2eeEnvelopeIn | None = None

    @model_validator(mode="after")
    def content(self):
        if self.text and self.e2ee:
            raise ValueError("Edit must be plaintext or e2ee, not both")
        if not self.text and not self.e2ee:
            raise ValueError("Edit requires text or e2ee envelope")
        return self


class ReactionInput(BaseModel):
    reaction: str = Field(min_length=1, max_length=64)


class SequenceInput(BaseModel):
    sequence: int = Field(ge=1)
