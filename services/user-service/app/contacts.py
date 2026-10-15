import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, require_authenticated_context
from app.contacts_runtime import identity_lookup, rate_limit
from app.main import (
    Contact,
    User,
    UserBlock,
    UserPrivacySettings,
    active_avatar,
    current_user,
    db,
    internal,
)


class PrivateRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request):
            try:
                return await original(request)
            except SQLAlchemyError:
                return JSONResponse(
                    status_code=503, content={"detail": "Contact storage is unavailable."}
                )
            except RequestValidationError as exc:
                return JSONResponse(status_code=422, content={"detail": exc.errors()})

        return handler


router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"], route_class=PrivateRoute)

_PHONE_DISPLAY = re.compile(r"^[\d\s+\-().]{0,40}$")


class PhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str = Field(min_length=3, max_length=64)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")


class ContactCreate(PhoneInput):
    local_label: str | None = Field(None, max_length=200)
    given_name: str | None = Field(None, max_length=100)
    family_name: str | None = Field(None, max_length=100)
    phone_display: str | None = Field(None, max_length=40)

    @field_validator("given_name", "family_name", "local_label", mode="before")
    @classmethod
    def empty_name_to_none(cls, value: str | None):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("phone_display", mode="before")
    @classmethod
    def normalize_phone_display(cls, value: str | None):
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        cleaned = cleaned[:40]
        if not _PHONE_DISPLAY.fullmatch(cleaned):
            raise ValueError("Use digits, spaces, +, -, (), or . only.")
        return cleaned


class ContactPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    local_label: str | None = Field(None, max_length=200)
    given_name: str | None = Field(None, max_length=100)
    family_name: str | None = Field(None, max_length=100)
    phone_display: str | None = Field(None, max_length=40)
    phone: str | None = Field(None, min_length=3, max_length=64)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")

    @field_validator("given_name", "family_name", "local_label", mode="before")
    @classmethod
    def empty_name_to_none(cls, value: str | None):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("phone_display", mode="before")
    @classmethod
    def normalize_phone_display(cls, value: str | None):
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        cleaned = cleaned[:40]
        if not _PHONE_DISPLAY.fullmatch(cleaned):
            raise ValueError("Use digits, spaces, +, -, (), or . only.")
        return cleaned

    @model_validator(mode="after")
    def safe_fields(self):
        if ("phone" in self.model_fields_set and self.phone is None) or (
            self.country and not self.phone
        ):
            raise ValueError("A replacement phone is required")
        return self


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contacts: list[PhoneInput] = Field(min_length=1, max_length=20)


class SafeUser(BaseModel):
    user_id: uuid.UUID
    display_name: str
    avatar_media_id: uuid.UUID | None
    phone_verified: bool


class SavedContact(BaseModel):
    id: uuid.UUID
    local_label: str | None
    given_name: str | None
    family_name: str | None
    phone_display: str | None
    created_at: datetime
    updated_at: datetime
    matched_user: SafeUser | None


class ContactPage(BaseModel):
    items: list[SavedContact]
    next_cursor: uuid.UUID | None


class MatchItem(BaseModel):
    input_index: int
    matched_user: SafeUser | None


class MatchResponse(BaseModel):
    results: list[MatchItem]


async def owner(session, context):
    user = await current_user(session, context)
    if user.status != "ACTIVE" or user.deleted_at is not None:
        raise HTTPException(403, "Account unavailable.")
    return user


def _clean_piece(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:limit]


def _phone_display(value: str | None) -> str | None:
    cleaned = _clean_piece(value, 40)
    if cleaned is None:
        return None
    if not _PHONE_DISPLAY.fullmatch(cleaned):
        raise HTTPException(422, "Invalid phone display.")
    return cleaned


def _compose_label(
    given: str | None,
    family: str | None,
    local_label: str | None,
) -> str | None:
    parts = [p for p in (given, family) if p]
    if parts:
        return " ".join(parts)
    return local_label


def _name_fields(body, existing: Contact | None = None):
    given = (
        _clean_piece(body.given_name, 100)
        if "given_name" in body.model_fields_set
        else (existing.given_name if existing else None)
    )
    family = (
        _clean_piece(body.family_name, 100)
        if "family_name" in body.model_fields_set
        else (existing.family_name if existing else None)
    )
    local = (
        _clean_piece(body.local_label, 200)
        if "local_label" in body.model_fields_set
        else (existing.local_label if existing else None)
    )
    label = _compose_label(given, family, local)
    return given, family, label


async def eligible(session, requester, results):
    ids = {uuid.UUID(r["identity_id"]) for r in results if r.get("identity_id")}
    if not ids:
        return {}
    blocked = (
        select(UserBlock.id)
        .where(
            or_(
                and_(
                    UserBlock.blocker_user_id == requester.id, UserBlock.blocked_user_id == User.id
                ),
                and_(
                    UserBlock.blocker_user_id == User.id, UserBlock.blocked_user_id == requester.id
                ),
            )
        )
        .exists()
    )
    rows = (
        await session.execute(
            select(User, UserPrivacySettings)
            .join(UserPrivacySettings, UserPrivacySettings.user_id == User.id)
            .where(
                User.identity_id.in_(ids),
                User.id != requester.id,
                User.status == "ACTIVE",
                User.deleted_at.is_(None),
                UserPrivacySettings.discoverable.is_(True),
                ~blocked,
            )
        )
    ).all()
    profiles = {str(u.identity_id): (u, p) for u, p in rows}
    return {
        r["digest"]: {
            "user_id": str(profiles[r["identity_id"]][0].id),
            "display_name": profiles[r["identity_id"]][0].display_name,
            "avatar_media_id": str(active_avatar(profiles[r["identity_id"]][0]))
            if active_avatar(profiles[r["identity_id"]][0])
            and profiles[r["identity_id"]][1].profile_photo_visibility == "EVERYONE"
            else None,
            "phone_verified": bool(r["phone_verified"]),
        }
        for r in results
        if r.get("identity_id") in profiles
    }


async def render(request, session, user, contacts):
    if not contacts:
        return []
    results = await identity_lookup(request, {"digests": [c.phone_digest for c in contacts]})
    matches = await eligible(session, user, results)
    return [
        {
            "id": str(c.id),
            "local_label": c.local_label,
            "given_name": c.given_name,
            "family_name": c.family_name,
            "phone_display": c.phone_display,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "matched_user": matches.get(c.phone_digest),
        }
        for c in contacts
    ]


@router.post("/match", response_model=MatchResponse)
async def match(
    body: MatchRequest,
    request: Request,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await owner(session, context)
    await rate_limit(request, context.identity_id, len(body.contacts))
    results = await identity_lookup(request, {"phones": [c.model_dump() for c in body.contacts]})
    matches = await eligible(session, user, results)
    seen = set()
    output = []
    for index, r in enumerate(results):
        if r["digest"] not in seen:
            seen.add(r["digest"])
            output.append({"input_index": index, "matched_user": matches.get(r["digest"])})
    return {"results": output}


@router.get("", response_model=ContactPage)
async def listing(
    request: Request,
    limit: int = Query(20, ge=1, le=50),
    after: uuid.UUID | None = None,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    if set(request.query_params) - {"limit", "after"}:
        raise HTTPException(422, "Unsupported contact query.")
    user = await owner(session, context)
    await rate_limit(request, context.identity_id)
    query = (
        select(Contact)
        .where(Contact.owner_user_id == user.id)
        .order_by(Contact.id)
        .limit(limit + 1)
    )
    if after:
        query = query.where(Contact.id > after)
    rows = list((await session.scalars(query)).all())
    return {
        "items": await render(request, session, user, rows[:limit]),
        "next_cursor": str(rows[limit - 1].id) if len(rows) > limit else None,
    }


@router.post("", response_model=SavedContact)
async def create(
    body: ContactCreate,
    request: Request,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await owner(session, context)
    await rate_limit(request, context.identity_id, 1)
    result = await identity_lookup(
        request, {"phones": [{"phone": body.phone, "country": body.country}]}
    )
    given, family, label = _name_fields(body)
    display = _phone_display(body.phone_display) if body.phone_display else None
    values = {
        "id": uuid.uuid4(),
        "owner_user_id": user.id,
        "phone_digest": result[0]["digest"],
        "local_label": label,
        "given_name": given,
        "family_name": family,
        "phone_display": display,
    }
    statement = insert(Contact).values(**values)
    updates = {
        "phone_digest": values["phone_digest"],
        "local_label": values["local_label"],
        "given_name": values["given_name"],
        "family_name": values["family_name"],
        "phone_display": values["phone_display"],
        "updated_at": func.now(),
    }
    cid = await session.scalar(
        statement.on_conflict_do_update(
            constraint="contact_owner_phone_unique", set_=updates
        ).returning(Contact.id)
    )
    await session.commit()
    row = await session.get(Contact, cid)
    return (await render(request, session, user, [row]))[0]


async def owned(session, user, cid):
    row = await session.scalar(
        select(Contact).where(Contact.id == cid, Contact.owner_user_id == user.id)
    )
    if row is None:
        raise HTTPException(404, "Contact unavailable.")
    return row


@router.get("/{contact_id}", response_model=SavedContact)
async def get(
    contact_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await owner(session, context)
    row = await owned(session, user, contact_id)
    await rate_limit(request, context.identity_id)
    return (await render(request, session, user, [row]))[0]


@router.patch("/{contact_id}", response_model=SavedContact)
async def update(
    contact_id: uuid.UUID,
    body: ContactPatch,
    request: Request,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await owner(session, context)
    row = await owned(session, user, contact_id)
    await rate_limit(request, context.identity_id, 1 if body.phone else 0)
    if body.phone:
        result = await identity_lookup(
            request, {"phones": [{"phone": body.phone, "country": body.country}]}
        )
        row.phone_digest = result[0]["digest"]
    if (
        "local_label" in body.model_fields_set
        or "given_name" in body.model_fields_set
        or "family_name" in body.model_fields_set
    ):
        given, family, label = _name_fields(body, row)
        row.given_name = given
        row.family_name = family
        row.local_label = label
    if "phone_display" in body.model_fields_set:
        row.phone_display = _phone_display(body.phone_display)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "This contact is already saved.") from None
    await session.refresh(row)
    return (await render(request, session, user, [row]))[0]


@router.delete("/{contact_id}")
async def delete(
    contact_id: uuid.UUID,
    request: Request,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await owner(session, context)
    row = await owned(session, user, contact_id)
    await rate_limit(request, context.identity_id)
    await session.delete(row)
    await session.commit()
    return {"deleted": True}


internal_router = APIRouter(prefix="/internal/v1/contacts", dependencies=[Depends(internal)])


class ContactAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: uuid.UUID
    contact_id: uuid.UUID


@internal_router.post("/authorize", include_in_schema=False)
async def authorize_contact(
    body: ContactAuthorization, request: Request, session: AsyncSession = Depends(db)
):
    requester = await session.scalar(
        select(User).where(
            User.identity_id == body.identity_id, User.status == "ACTIVE", User.deleted_at.is_(None)
        )
    )
    contact = (
        await session.scalar(
            select(Contact).where(
                Contact.id == body.contact_id, Contact.owner_user_id == requester.id
            )
        )
        if requester
        else None
    )
    if contact is None:
        raise HTTPException(404, "Contact unavailable.")
    results = await identity_lookup(request, {"digests": [contact.phone_digest]})
    matches = await eligible(session, requester, results)
    match = matches.get(contact.phone_digest)
    if not match:
        raise HTTPException(404, "Contact unavailable.")
    target = await session.get(User, uuid.UUID(match["user_id"]))
    return {
        "identity_id": str(target.identity_id),
        "display_name": match["display_name"],
        "avatar_media_id": match["avatar_media_id"],
        "user_id": str(target.id),
    }


class CommunicationAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: uuid.UUID
    peer_identity_id: uuid.UUID


@internal_router.post("/communication", include_in_schema=False)
async def authorize_communication(
    body: CommunicationAuthorization, session: AsyncSession = Depends(db)
):
    users = (
        await session.scalars(
            select(User).where(
                User.identity_id.in_([body.identity_id, body.peer_identity_id]),
                User.status == "ACTIVE",
                User.deleted_at.is_(None),
            )
        )
    ).all()
    if len(users) != 2:
        return {"allowed": False}
    ids = [u.id for u in users]
    blocked = await session.scalar(
        select(UserBlock.id).where(
            UserBlock.blocker_user_id.in_(ids), UserBlock.blocked_user_id.in_(ids)
        )
    )
    return {"allowed": blocked is None}


class ParticipantProfiles(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_ids: list[uuid.UUID] = Field(max_length=200)


@internal_router.post("/profiles", include_in_schema=False)
async def participant_profiles(body: ParticipantProfiles, session: AsyncSession = Depends(db)):
    rows = (
        await session.execute(
            select(User, UserPrivacySettings)
            .join(UserPrivacySettings, UserPrivacySettings.user_id == User.id)
            .where(
                User.identity_id.in_(body.identity_ids),
                User.status == "ACTIVE",
                User.deleted_at.is_(None),
            )
        )
    ).all()
    return {
        str(user.identity_id): {
            "title": user.display_name,
            "avatar_media_id": str(active_avatar(user))
            if active_avatar(user) and privacy.profile_photo_visibility == "EVERYONE"
            else None,
        }
        for user, privacy in rows
    }


class PresencePermission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity_id: uuid.UUID
    target_identity_id: uuid.UUID


@internal_router.post("/presence-permission", include_in_schema=False)
async def presence_permission(
    body: PresencePermission, request: Request, session: AsyncSession = Depends(db)
):
    from app.profile_photos import visible

    viewer = await session.scalar(select(User).where(User.identity_id == body.identity_id))
    target = await session.scalar(select(User).where(User.identity_id == body.target_identity_id))
    if viewer is None or target is None:
        return {"allowed": False}
    return {"allowed": await visible(session, viewer, target, request, "online_status_visibility")}
