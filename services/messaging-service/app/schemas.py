from uuid import UUID

from pydantic import BaseModel, Field


class SendMessage(BaseModel):
    client_message_id: UUID
    type: str = "TEXT"
    text: str = Field(min_length=1, max_length=10000)
    reply_to_message_id: UUID | None = None


class EditMessage(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class ReactionInput(BaseModel):
    reaction: str = Field(min_length=1, max_length=64)


class SequenceInput(BaseModel):
    sequence: int = Field(ge=1)
