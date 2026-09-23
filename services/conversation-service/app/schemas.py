from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DirectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_id: UUID


class GroupIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    member_ids: list[UUID] = Field(min_length=1, max_length=10000)


class MemberIds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_ids: list[UUID] = Field(min_length=1, max_length=10000)


class Transfer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_id: UUID


class UpdateConversation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    avatar_media_id: UUID | None = None


class StateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_archived: bool | None = None
    is_pinned: bool | None = None
    muted_until: datetime | None = None
    is_muted_forever: bool | None = None
    notification_level: str | None = Field(None, pattern="^(ALL|MENTIONS|NONE)$")
