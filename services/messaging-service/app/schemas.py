from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SendMessage(BaseModel):
    client_message_id: UUID
    type: str = "TEXT"
    text: str | None = Field(default=None, min_length=1, max_length=10000)
    media_id: UUID | None = None

    @model_validator(mode="after")
    def content(self):
        if self.type == "TEXT":
            if not self.text or not self.text.strip() or self.media_id:
                raise ValueError("Text content is required without media")
        elif self.type == "SYSTEM":
            return self
        elif self.type not in {"IMAGE", "VIDEO", "AUDIO", "VOICE", "DOCUMENT"} or not self.media_id:
            raise ValueError("A supported media type and media_id are required")
        return self

    reply_to_message_id: UUID | None = None


class EditMessage(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class ReactionInput(BaseModel):
    reaction: str = Field(min_length=1, max_length=64)


class SequenceInput(BaseModel):
    sequence: int = Field(ge=1)
