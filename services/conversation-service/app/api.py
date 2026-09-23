from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DomainError, settings
from app.db import db
from app.models import (
    BlockProjection,
    Conversation,
    ConversationMember,
    CStatus,
    CType,
    MemberState,
    MRole,
    MStatus,
)
from app.schemas import DirectIn, GroupIn, MemberIds, StateIn, Transfer, UpdateConversation
from app.services import Authorization, ConversationService, event

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
internal_router = APIRouter(prefix="/internal/v1/conversations", tags=["internal"])


async def principal(
    x_internal_service_token: str = Header(...),
    x_organization_id: UUID = Header(...),
    x_member_id: UUID = Header(...),
):
    if x_internal_service_token != settings().internal_service_token:
        raise DomainError("NOT_AUTHENTICATED", "Authentication is required.", 401)
    return x_organization_id, x_member_id


async def internal_service(x_internal_service_token: str = Header(...)):
    if x_internal_service_token != settings().internal_service_token:
        raise DomainError("NOT_AUTHENTICATED", "Authentication is required.", 401)


async def get_conversation(cid, org, db):
    c = (
        await db.execute(
            select(Conversation)
            .where(Conversation.id == cid, Conversation.organization_id == org)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if not c:
        raise DomainError("CONVERSATION_NOT_FOUND", "Conversation was not found.", 404)
    return c


def out(c, m=None, s=None, count=None):
    return {
        "id": str(c.id),
        "type": c.type,
        "title": c.title,
        "description": c.description,
        "avatar_media_id": str(c.avatar_media_id) if c.avatar_media_id else None,
        "status": c.status,
        "role": m.role if m else None,
        "state": {
            "is_archived": s.is_archived,
            "is_pinned": s.is_pinned,
            "muted_until": s.muted_until,
            "is_muted_forever": s.is_muted_forever,
            "notification_level": s.notification_level,
        }
        if s
        else None,
        "member_count": count,
    }


@router.post("/direct", status_code=201)
async def direct(
    payload: DirectIn, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c, created = await ConversationService().direct(
            session, *p, payload.member_id, request.state.correlation_id
        )
    return out(c) | {"created": created}


@router.post("/groups", status_code=201)
async def group(
    payload: GroupIn, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await ConversationService().group(session, *p, payload, request.state.correlation_id)
    return out(c)


@router.get("")
async def list_conversations(
    type: CType | None = None,
    archived: bool | None = None,
    pinned: bool | None = None,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    org, mid = p
    q = (
        select(Conversation, ConversationMember, MemberState, func.count(ConversationMember.id))
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .join(
            MemberState,
            (MemberState.conversation_id == Conversation.id) & (MemberState.member_id == mid),
        )
        .where(
            ConversationMember.member_id == mid,
            ConversationMember.status == MStatus.ACTIVE,
            Conversation.organization_id == org,
        )
        .group_by(Conversation.id, ConversationMember.id, MemberState.id)
    )
    if type:
        q = q.where(Conversation.type == type)
    if archived is not None:
        q = q.where(MemberState.is_archived == archived)
    if pinned is not None:
        q = q.where(MemberState.is_pinned == pinned)
    return [out(c, m, s, count) for c, m, s, count in (await session.execute(q)).all()]


@router.get("/{cid}")
async def get(cid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    c = await get_conversation(cid, p[0], session)
    m = await ConversationService().mine(session, c.id, p[1])
    Authorization.view(m)
    s = (
        await session.execute(
            select(MemberState).where(
                MemberState.conversation_id == c.id, MemberState.member_id == p[1]
            )
        )
    ).scalar_one()
    return out(c, m, s)


@router.post("/{cid}/members")
async def add(
    cid: UUID,
    payload: MemberIds,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        members = await ConversationService().add(
            session, c, p[1], payload.member_ids, request.state.correlation_id
        )
    return {"added_member_ids": members}


@router.delete("/{cid}/members/{mid}")
async def remove(
    cid: UUID,
    mid: UUID,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().remove(session, c, p[1], mid, request.state.correlation_id)
    return {"status": "REMOVED"}


@router.post("/{cid}/leave")
async def leave(
    cid: UUID, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().remove(
            session, c, p[1], p[1], request.state.correlation_id, True
        )
    return {"status": "LEFT"}


@router.post("/{cid}/close")
async def close(
    cid: UUID, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.manage(await ConversationService().mine(session, c.id, p[1]))
        if c.status != CStatus.CLOSED:
            c.status, c.closed_at = CStatus.CLOSED, datetime.now(UTC)
            await event(
                session, "conversation.closed.v1", c, request.state.correlation_id, ["status"]
            )
    return out(c)


@router.get("/{cid}/members")
async def members(cid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    c = await get_conversation(cid, p[0], session)
    Authorization.view(await ConversationService().mine(session, c.id, p[1]))
    rows = (
        (
            await session.execute(
                select(ConversationMember)
                .where(ConversationMember.conversation_id == c.id)
                .order_by(ConversationMember.joined_at)
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "member_id": str(x.member_id),
            "user_id": str(x.user_id) if x.user_id else None,
            "role": x.role,
            "status": x.status,
        }
        for x in rows
    ]


@router.post("/{cid}/members/{mid}/promote")
async def promote(cid: UUID, mid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.owner(await ConversationService().mine(session, c.id, p[1]))
        m = await ConversationService().mine(session, c.id, mid)
        Authorization.view(m)
        if m.role == MRole.OWNER:
            raise DomainError("OWNER_ROLE_IMMUTABLE", "Ownership requires transfer.", 409)
        old_role = m.role
        m.role = MRole.ADMIN
        await event(session, "conversation.member_role_changed.v1", c, "", ["members"], m, old_role)
    return {"status": "ADMIN"}


@router.post("/{cid}/members/{mid}/demote")
async def demote(cid: UUID, mid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.owner(await ConversationService().mine(session, c.id, p[1]))
        m = await ConversationService().mine(session, c.id, mid)
        Authorization.view(m)
        if m.role == MRole.OWNER:
            raise DomainError("OWNER_ROLE_IMMUTABLE", "Ownership requires transfer.", 409)
        old_role = m.role
        m.role = MRole.MEMBER
        await event(session, "conversation.member_role_changed.v1", c, "", ["members"], m, old_role)
    return {"status": "MEMBER"}


@router.post("/{cid}/transfer-ownership")
async def transfer(
    cid: UUID,
    payload: Transfer,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().transfer(
            session, c, p[1], payload.member_id, request.state.correlation_id
        )
    return {"status": "TRANSFERRED"}


@router.patch("/{cid}")
async def update(
    cid: UUID,
    payload: UpdateConversation,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups can be updated.", 422)
        Authorization.manage(await ConversationService().mine(session, c.id, p[1]))
        for k, v in payload.model_dump(exclude_unset=True).items():
            if k == "title" and (v is None or not v.strip()):
                raise DomainError("GROUP_TITLE_INVALID", "A group title is required.", 422)
            setattr(c, k, v.strip() if k == "title" and v else v)
        await event(
            session, "conversation.updated.v1", c, request.state.correlation_id, ["metadata"]
        )
    return out(c)


@router.patch("/{cid}/state")
async def state(
    cid: UUID, payload: StateIn, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.view(await ConversationService().mine(session, c.id, p[1]))
        s = (
            await session.execute(
                select(MemberState)
                .where(MemberState.conversation_id == c.id, MemberState.member_id == p[1])
                .with_for_update()
            )
        ).scalar_one()
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        member = await ConversationService().mine(session, c.id, p[1])
        await event(session, "conversation.state_updated.v1", c, "", ["state"], member, state=s)
    return {"status": "UPDATED"}


@internal_router.post("/{cid}/authorize")
async def authorize_send(
    cid: UUID,
    body: dict,
    _: None = Depends(internal_service),
    session: AsyncSession = Depends(db),
):
    organization_id, member_id = UUID(body["organization_id"]), UUID(body["member_id"])
    c = await get_conversation(cid, organization_id, session)
    member = await ConversationService().mine(session, c.id, member_id)
    allowed = c.status == "ACTIVE" and member is not None and member.status == MStatus.ACTIVE
    if allowed and c.type == CType.DIRECT:
        peers = (
            await session.scalars(
                select(ConversationMember).where(
                    ConversationMember.conversation_id == c.id,
                    ConversationMember.member_id != member_id,
                )
            )
        ).all()
        for peer in peers:
            blocked = await session.scalar(
                select(BlockProjection.id).where(
                    (
                        (BlockProjection.blocker_user_id == member.user_id)
                        & (BlockProjection.blocked_user_id == peer.user_id)
                    )
                    | (
                        (BlockProjection.blocker_user_id == peer.user_id)
                        & (BlockProjection.blocked_user_id == member.user_id)
                    )
                )
            )
            allowed = allowed and not bool(blocked)
    return {
        "allowed": allowed,
        "conversation_id": str(c.id),
        "organization_id": str(c.organization_id),
        "conversation_type": c.type,
        "member_id": str(member_id),
        "user_id": str(member.user_id) if member and member.user_id else None,
        "member_status": member.status if member else None,
    }
