from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

EVENT_TYPES = frozenset(
    f"{aggregate}.{action}.v1"
    for aggregate, actions in {
        "organization": ["created", "updated", "suspended", "disabled", "deleted"],
        "branch": ["created", "updated", "disabled", "deleted"],
        "team": ["created", "updated", "disabled", "deleted"],
        "member": [
            "created",
            "updated",
            "activated",
            "suspended",
            "left",
            "removed",
            "role_changed",
        ],
        "invitation": ["created", "accepted", "revoked", "expired"],
        "team_membership": ["created", "left"],
        "branch_membership": ["created", "left", "updated"],
        "organization_settings": ["updated"],
        "role": ["created", "updated"],
    }.items()
    for action in actions
)


class ChangePayload(BaseModel):
    """Minimal invalidation contract; consumers resolve authorized details through APIs."""

    model_config = ConfigDict(extra="forbid")
    resource_id: UUID
    changed_fields: list[str]
    status: str | None = None


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    event_type: str
    event_version: Literal[1] = 1
    occurred_at: datetime
    producer: Literal["organization-service"] = "organization-service"
    organization_id: UUID | None
    aggregate_id: UUID
    correlation_id: str
    payload: ChangePayload

    @field_validator("event_type")
    @classmethod
    def registered_event_type(cls, value: str) -> str:
        if value not in EVENT_TYPES:
            raise ValueError("Unknown event contract")
        return value
