from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

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
MEMBER_EVENT_TYPES_V2 = frozenset(
    f"member.{action}.v2"
    for action in (
        "created",
        "updated",
        "activated",
        "suspended",
        "left",
        "removed",
        "role_changed",
    )
)
EVENT_TYPES = EVENT_TYPES | MEMBER_EVENT_TYPES_V2


class ChangePayload(BaseModel):
    """Minimal invalidation contract; consumers resolve authorized details through APIs."""

    model_config = ConfigDict(extra="forbid")
    resource_id: UUID
    changed_fields: list[str]
    status: str | None = None


class MembershipPayload(ChangePayload):
    """Authoritative organization membership identity for downstream projections."""

    member_id: UUID
    user_id: UUID | None
    participant_kind: Literal["HUMAN", "UNLINKED_MEMBER"]


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    event_type: str
    event_version: Literal[1, 2] = 1
    occurred_at: datetime
    producer: Literal["organization-service"] = "organization-service"
    organization_id: UUID | None
    aggregate_id: UUID
    correlation_id: str
    payload: ChangePayload | MembershipPayload

    @model_validator(mode="after")
    def validate_contract(self):
        if self.event_type not in EVENT_TYPES:
            raise ValueError("Unknown event contract")
        if self.event_type in MEMBER_EVENT_TYPES_V2:
            if self.event_version != 2 or not isinstance(self.payload, MembershipPayload):
                raise ValueError("member v2 events require MembershipPayload and event_version 2")
            if self.organization_id is None:
                raise ValueError("member v2 events require organization_id")
        elif self.event_version != 1:
            raise ValueError("v1 events require event_version 1")
        return self
