from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select, text

from app.core import DomainError, settings
from app.models import (
    BlockProjection,
    Conversation,
    ConversationMember,
    ConversationSettings,
    CStatus,
    CType,
    MemberProjection,
    MemberState,
    MRole,
    MStatus,
    OutboxEvent,
)


def direct_key(a, b):
    return ":".join(sorted([str(a), str(b)]))


async def resolve_contact_identity(actor, contact_id) -> UUID:
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            response = await client.post(
                settings().user_service_url.rstrip("/") + "/internal/v1/contacts/authorize",
                headers={"X-Internal-Service-Token": settings().internal_service_token},
                json={"identity_id": str(actor), "contact_id": str(contact_id)},
            )
        if response.status_code in {403, 404}:
            raise DomainError("CONTACT_UNAVAILABLE", "Contact is unavailable.", 404)
        response.raise_for_status()
        return UUID(response.json()["identity_id"])
    except DomainError:
        raise
    except (httpx.HTTPError, ValueError, KeyError):
        raise DomainError(
            "CONTACT_UNAVAILABLE", "Contact authorization is unavailable.", 503
        ) from None


async def blocked_between(db, user_a: UUID, user_b: UUID) -> bool:
    if user_a == user_b:
        return False
    blocked = await db.scalar(
        select(BlockProjection.id).where(
            (
                (BlockProjection.blocker_user_id == user_a)
                & (BlockProjection.blocked_user_id == user_b)
            )
            | (
                (BlockProjection.blocker_user_id == user_b)
                & (BlockProjection.blocked_user_id == user_a)
            )
        )
    )
    return bool(blocked)


async def event(
    db,
    typ,
    conversation,
    correlation,
    fields=[],
    member=None,
    old_role=None,
    old_member=None,
    state=None,
):
    members = (
        (
            await db.execute(
                select(ConversationMember).where(
                    ConversationMember.conversation_id == conversation.id
                )
            )
        )
        .scalars()
        .all()
    )
    payload = {
        "conversation_id": str(conversation.id),
        "organization_id": str(conversation.organization_id)
        if conversation.organization_id
        else None,
        "scope": "WORKSPACE" if conversation.organization_id else "PERSONAL",
        "type": conversation.type,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "changed_fields": fields,
        "members": [
            {
                "member_id": str(m.member_id),
                "user_id": str(m.user_id) if m.user_id else None,
                "participant_kind": "HUMAN" if m.user_id else "UNLINKED_MEMBER",
                "role": m.role,
                "status": m.status,
            }
            for m in members
        ],
    }
    if member is not None:
        payload.update(
            {
                "member_id": str(member.member_id),
                "user_id": str(member.user_id) if member.user_id else None,
                "participant_kind": "HUMAN" if member.user_id else "UNLINKED_MEMBER",
                "role": member.role,
                "resulting_status": member.status,
            }
        )
    if old_role is not None:
        payload.update({"old_role": old_role, "new_role": member.role})
    if typ == "conversation.ownership_transferred.v1" and member is not None:
        previous = old_member
        payload.update(
            {
                "old_owner_member_id": str(previous.member_id) if previous else None,
                "new_owner_member_id": str(member.member_id),
                "old_owner_user_id": str(previous.user_id)
                if previous and previous.user_id
                else None,
                "new_owner_user_id": str(member.user_id) if member.user_id else None,
            }
        )
    if typ == "conversation.closed.v1":
        payload["closed_at"] = (
            conversation.closed_at.isoformat() if conversation.closed_at else None
        )
    if typ == "conversation.deleted.v1":
        payload["deleted_at"] = (
            conversation.deleted_at.isoformat() if conversation.deleted_at else None
        )
    if typ == "conversation.state_updated.v1" and state is not None:
        payload.update(
            {
                "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                "is_archived": state.is_archived,
                "is_pinned": state.is_pinned,
                "muted_until": state.muted_until.isoformat() if state.muted_until else None,
                "notification_level": state.notification_level,
            }
        )
    db.add(
        OutboxEvent(
            event_type=typ,
            aggregate_id=conversation.id,
            organization_id=conversation.organization_id,
            correlation_id=correlation,
            payload=payload,
        )
    )


class Authorization:
    @staticmethod
    def view(m):
        if not m or m.status != MStatus.ACTIVE:
            raise DomainError("CONVERSATION_NOT_FOUND", "Conversation was not found.", 404)

    @staticmethod
    def manage(m):
        Authorization.view(m)
        if m.role not in {MRole.OWNER, MRole.ADMIN}:
            raise DomainError(
                "CONVERSATION_PERMISSION_DENIED", "Conversation management is not permitted.", 403
            )

    @staticmethod
    def owner(m):
        Authorization.view(m)
        if m.role != MRole.OWNER:
            raise DomainError(
                "CONVERSATION_OWNER_REQUIRED", "Only the group owner may perform this action.", 403
            )


class ConversationService:
    async def ensure_workspace_member_active(self, db, organization_id: UUID, member_id: UUID):
        member = (
            await db.execute(
                select(MemberProjection).where(
                    MemberProjection.organization_id == organization_id,
                    MemberProjection.member_id == member_id,
                    MemberProjection.status == "ACTIVE",
                )
            )
        ).scalar_one_or_none()
        if member is None:
            raise DomainError("CONVERSATION_NOT_FOUND", "Conversation was not found.", 404)

    async def participant_user_id(self, db, conversation: Conversation, participant_id: UUID):
        if conversation.organization_id is None:
            return participant_id
        return await self.member_user_id(db, conversation.organization_id, participant_id)

    async def personal_direct(self, db, actor, contact_id, correlation):
        target = await resolve_contact_identity(actor, contact_id)
        if actor == target:
            raise DomainError("CONTACT_UNAVAILABLE", "Contact is unavailable.", 404)
        if await blocked_between(db, actor, target):
            raise DomainError(
                "DIRECT_CONVERSATION_BLOCKED", "Direct messaging is unavailable.", 403
            )
        key = direct_key(actor, target)
        # Serialize both directions; DB unique index remains the final invariant.
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": "personal:" + key},
        )
        existing = await db.scalar(
            select(Conversation).where(
                Conversation.organization_id.is_(None), Conversation.direct_key == key
            )
        )
        if existing:
            return existing, False
        c = Conversation(
            organization_id=None,
            type=CType.DIRECT,
            direct_key=key,
            created_by_member_id=actor,
            status=CStatus.ACTIVE,
        )
        db.add(c)
        await db.flush()
        for identity in (actor, target):
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=None,
                    member_id=identity,
                    user_id=identity,
                    role=MRole.MEMBER,
                    added_by_member_id=actor,
                )
            )
            db.add(MemberState(conversation_id=c.id, member_id=identity))
        await event(db, "conversation.created.v1", c, correlation)
        return c, True

    async def member_user_id(self, db, organization_id, member_id):
        """Resolve a human member from this service's local organization projection."""
        member = (
            await db.execute(
                select(MemberProjection).where(
                    MemberProjection.organization_id == organization_id,
                    MemberProjection.member_id == member_id,
                    MemberProjection.status == "ACTIVE",
                )
            )
        ).scalar_one_or_none()
        if member is None or member.user_id is None:
            raise DomainError(
                "MEMBER_IDENTITY_UNAVAILABLE",
                "A human user identity is required for conversation membership.",
                409,
            )
        return member.user_id

    async def mine(self, db, cid, mid):
        return (
            await db.execute(
                select(ConversationMember)
                .where(
                    ConversationMember.conversation_id == cid, ConversationMember.member_id == mid
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

    async def direct(self, db, org, actor, target, correlation):
        if actor == target:
            raise DomainError(
                "DIRECT_SELF_NOT_ALLOWED", "A direct conversation requires another member.", 422
            )
        member_users = {
            member_id: await self.member_user_id(db, org, member_id)
            for member_id in (actor, target)
        }
        actor_user, target_user = member_users[actor], member_users[target]
        blocked = await db.scalar(
            select(BlockProjection.id).where(
                (
                    (BlockProjection.blocker_user_id == actor_user)
                    & (BlockProjection.blocked_user_id == target_user)
                )
                | (
                    (BlockProjection.blocker_user_id == target_user)
                    & (BlockProjection.blocked_user_id == actor_user)
                )
            )
        )
        if blocked:
            raise DomainError(
                "DIRECT_CONVERSATION_BLOCKED", "Direct messaging is unavailable.", 403
            )
        key = direct_key(actor, target)
        c = (
            await db.execute(
                select(Conversation)
                .where(Conversation.organization_id == org, Conversation.direct_key == key)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if c:
            return c, False
        c = Conversation(
            organization_id=org,
            type=CType.DIRECT,
            direct_key=key,
            created_by_member_id=actor,
            status=CStatus.ACTIVE,
        )
        db.add(c)
        await db.flush()
        for m in (actor, target):
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=org,
                    member_id=m,
                    user_id=member_users[m],
                    role=MRole.MEMBER,
                    added_by_member_id=actor,
                )
            )
            db.add(MemberState(conversation_id=c.id, member_id=m))
        await event(db, "conversation.created.v1", c, correlation)
        return c, True

    async def group(self, db, org, actor, data, correlation):
        ids = list(dict.fromkeys([actor, *data.member_ids]))
        limit = settings().default_group_member_limit
        if len(ids) > limit:
            raise DomainError(
                "GROUP_MEMBER_LIMIT", "The group member limit would be exceeded.", 422
            )
        title = data.title.strip()
        if not title:
            raise DomainError("GROUP_TITLE_INVALID", "A group title is required.", 422)
        c = Conversation(
            organization_id=org,
            type=CType.GROUP,
            title=title,
            description=data.description,
            created_by_member_id=actor,
        )
        db.add(c)
        await db.flush()
        db.add(ConversationSettings(conversation_id=c.id))
        member_users = {
            member_id: await self.member_user_id(db, org, member_id) for member_id in ids
        }
        for m in ids:
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=org,
                    member_id=m,
                    user_id=member_users[m],
                    role=MRole.OWNER if m == actor else MRole.MEMBER,
                    added_by_member_id=actor,
                )
            )
            db.add(MemberState(conversation_id=c.id, member_id=m))
        await event(db, "conversation.created.v1", c, correlation)
        return c

    async def personal_group(self, db, actor, data, correlation):
        resolved = []
        for contact_id in dict.fromkeys(data.member_ids):
            identity = await resolve_contact_identity(actor, contact_id)
            if identity == actor:
                continue
            if await blocked_between(db, actor, identity):
                raise DomainError(
                    "DIRECT_CONVERSATION_BLOCKED", "Messaging is unavailable for a participant.", 403
                )
            resolved.append(identity)
        ids = list(dict.fromkeys([actor, *resolved]))
        limit = settings().default_group_member_limit
        if len(ids) > limit:
            raise DomainError(
                "GROUP_MEMBER_LIMIT", "The group member limit would be exceeded.", 422
            )
        title = data.title.strip()
        if not title:
            raise DomainError("GROUP_TITLE_INVALID", "A group title is required.", 422)
        for left, right in ((ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))):
            if await blocked_between(db, left, right):
                raise DomainError(
                    "DIRECT_CONVERSATION_BLOCKED", "Messaging is unavailable for a participant.", 403
                )
        c = Conversation(
            organization_id=None,
            type=CType.GROUP,
            title=title,
            description=data.description,
            created_by_member_id=actor,
        )
        db.add(c)
        await db.flush()
        db.add(ConversationSettings(conversation_id=c.id))
        for identity in ids:
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=None,
                    member_id=identity,
                    user_id=identity,
                    role=MRole.OWNER if identity == actor else MRole.MEMBER,
                    added_by_member_id=actor,
                )
            )
            db.add(MemberState(conversation_id=c.id, member_id=identity))
        await event(db, "conversation.created.v1", c, correlation)
        return c

    async def add(self, db, c, actor, ids, correlation):
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups can have members added.", 422)
        mine = await self.mine(db, c.id, actor)
        Authorization.view(mine)
        group_settings = (
            await db.execute(
                select(ConversationSettings).where(ConversationSettings.conversation_id == c.id)
            )
        ).scalar_one_or_none()
        if mine.role == MRole.MEMBER:
            if group_settings is None or not group_settings.members_can_invite:
                raise DomainError(
                    "CONVERSATION_PERMISSION_DENIED", "Conversation management is not permitted.", 403
                )
        elif group_settings and group_settings.only_admins_can_add_members:
            Authorization.manage(mine)
        current = (
            (
                await db.execute(
                    select(ConversationMember.member_id).where(
                        ConversationMember.conversation_id == c.id,
                        ConversationMember.status == MStatus.ACTIVE,
                    )
                )
            )
            .scalars()
            .all()
        )
        added = [x for x in dict.fromkeys(ids) if x not in current]
        if len(current) + len(added) > settings().default_group_member_limit:
            raise DomainError(
                "GROUP_MEMBER_LIMIT", "The group member limit would be exceeded.", 422
            )
        if c.organization_id is None:
            for contact_id in added:
                identity = await resolve_contact_identity(actor, contact_id)
                if await blocked_between(db, actor, identity):
                    raise DomainError(
                        "DIRECT_CONVERSATION_BLOCKED",
                        "Messaging is unavailable for a participant.",
                        403,
                    )
            added = [
                await resolve_contact_identity(actor, contact_id) for contact_id in added
            ]
            added = list(dict.fromkeys(added))
        member_users = {
            member_id: await self.participant_user_id(db, c, member_id) for member_id in added
        }
        for m in added:
            existing = await self.mine(db, c.id, m)
            if existing:
                existing.status = MStatus.ACTIVE
                existing.role = MRole.MEMBER
                existing.left_at = None
                existing.user_id = member_users[m]
                existing.added_by_member_id = actor
            else:
                db.add(
                    ConversationMember(
                        conversation_id=c.id,
                        organization_id=c.organization_id,
                        member_id=m,
                        user_id=member_users[m],
                        role=MRole.MEMBER,
                        added_by_member_id=actor,
                    )
                )
                db.add(MemberState(conversation_id=c.id, member_id=m))
        for member_id in added:
            await event(
                db,
                "conversation.member_added.v1",
                c,
                correlation,
                ["members"],
                await self.mine(db, c.id, member_id),
            )
        return added

    async def remove(self, db, c, actor, target, correlation, leave=False):
        mine = await self.mine(db, c.id, actor)
        target_m = await self.mine(db, c.id, target)
        Authorization.view(target_m)
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups support this operation.", 422)
        if not leave:
            Authorization.manage(mine)
        elif actor != target:
            raise DomainError(
                "CONVERSATION_PERMISSION_DENIED", "Cannot leave for another member.", 403
            )
        if target_m.role == MRole.OWNER:
            raise DomainError(
                "OWNERSHIP_TRANSFER_REQUIRED",
                "Transfer ownership before leaving or removing the owner.",
                409,
            )
        if not leave and mine.role == MRole.ADMIN and target_m.role in {MRole.ADMIN, MRole.OWNER}:
            raise DomainError(
                "CONVERSATION_PERMISSION_DENIED", "An admin cannot remove an admin or owner.", 403
            )
        target_m.status = MStatus.LEFT if leave else MStatus.REMOVED
        target_m.left_at = datetime.now(UTC)
        await event(
            db,
            "conversation.member_left.v1" if leave else "conversation.member_removed.v1",
            c,
            correlation,
            ["members"],
            target_m,
        )

    async def transfer(self, db, c, actor, target, correlation):
        Authorization.owner(await self.mine(db, c.id, actor))
        new = await self.mine(db, c.id, target)
        Authorization.view(new)
        old = await self.mine(db, c.id, actor)
        old_role = old.role
        old.role = MRole.ADMIN
        new.role = MRole.OWNER
        await event(
            db,
            "conversation.ownership_transferred.v1",
            c,
            correlation,
            ["members"],
            new,
            old_role,
            old,
        )

    async def revoke_org_conversations(
        self, db, organization_id: UUID, member_id: UUID, status: MStatus, correlation: str
    ):
        rows = (
            await db.execute(
                select(ConversationMember, Conversation)
                .join(Conversation, Conversation.id == ConversationMember.conversation_id)
                .where(
                    Conversation.organization_id == organization_id,
                    ConversationMember.organization_id == organization_id,
                    ConversationMember.member_id == member_id,
                    ConversationMember.status == MStatus.ACTIVE,
                )
                .with_for_update()
            )
        ).all()
        now = datetime.now(UTC)
        for member_row, conversation in rows:
            member_row.status = status
            member_row.left_at = now
            await event(
                db,
                "conversation.member_left.v1"
                if status == MStatus.LEFT
                else "conversation.member_removed.v1",
                conversation,
                correlation,
                ["members"],
                member_row,
            )

    async def delete_group(self, db, c, actor, correlation):
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups can be deleted.", 422)
        Authorization.owner(await self.mine(db, c.id, actor))
        if c.status == CStatus.DELETED:
            return
        c.status, c.deleted_at = CStatus.DELETED, datetime.now(UTC)
        await event(db, "conversation.deleted.v1", c, correlation, ["status"])
