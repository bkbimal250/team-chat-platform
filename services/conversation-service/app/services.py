from datetime import UTC, datetime

from sqlalchemy import select

from app.core import DomainError, settings
from app.models import (
    Conversation,
    ConversationMember,
    ConversationSettings,
    CStatus,
    CType,
    MemberState,
    MRole,
    MStatus,
    OutboxEvent,
)


def direct_key(a, b):
    return ":".join(sorted([str(a), str(b)]))


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
        "organization_id": str(conversation.organization_id),
        "type": conversation.type,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "changed_fields": fields,
        "members": [
            {
                "member_id": str(m.member_id),
                "user_id": str(m.user_id) if m.user_id else None,
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
        for m in ids:
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=org,
                    member_id=m,
                    role=MRole.OWNER if m == actor else MRole.MEMBER,
                    added_by_member_id=actor,
                )
            )
            db.add(MemberState(conversation_id=c.id, member_id=m))
        await event(db, "conversation.created.v1", c, correlation)
        return c

    async def add(self, db, c, actor, ids, correlation):
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups can have members added.", 422)
        Authorization.manage(await self.mine(db, c.id, actor))
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
        for m in added:
            db.add(
                ConversationMember(
                    conversation_id=c.id,
                    organization_id=c.organization_id,
                    member_id=m,
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
