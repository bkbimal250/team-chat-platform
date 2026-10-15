from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.fanout import NotificationFanout
from app.models import PendingInvitationNotification


class PendingInvitationRepository:
    def __init__(self, session):
        self.session = session

    async def upsert(
        self,
        *,
        invitation_id: UUID,
        organization_id: UUID,
        recipient_phone_e164: str | None,
        recipient_email: str | None,
    ) -> None:
        stmt = (
            insert(PendingInvitationNotification)
            .values(
                invitation_id=invitation_id,
                organization_id=organization_id,
                recipient_phone_e164=recipient_phone_e164,
                recipient_email=recipient_email,
            )
            .on_conflict_do_nothing(index_elements=["invitation_id"])
        )
        await self.session.execute(stmt)

    async def mark_fulfilled(self, invitation_id: UUID, user_id: UUID) -> None:
        row = await self.session.scalar(
            select(PendingInvitationNotification).where(
                PendingInvitationNotification.invitation_id == invitation_id
            )
        )
        if row is not None:
            row.fulfilled_user_id = user_id

    async def pending_for_phone(self, organization_id: UUID, phone_e164: str):
        return (
            await self.session.scalars(
                select(PendingInvitationNotification).where(
                    PendingInvitationNotification.organization_id == organization_id,
                    PendingInvitationNotification.recipient_phone_e164 == phone_e164,
                    PendingInvitationNotification.fulfilled_user_id.is_(None),
                )
            )
        ).all()

    async def pending_for_phone_any_org(self, phone_e164: str):
        return (
            await self.session.scalars(
                select(PendingInvitationNotification).where(
                    PendingInvitationNotification.recipient_phone_e164 == phone_e164,
                    PendingInvitationNotification.fulfilled_user_id.is_(None),
                )
            )
        ).all()


async def deliver_invitation(
    fanout: NotificationFanout,
    pending_repo: PendingInvitationRepository,
    projections,
    *,
    organization_id: UUID,
    invitation_id: UUID,
    recipient_user_id: UUID | None,
    recipient_phone_e164: str | None,
    recipient_email: str | None,
) -> bool:
    await pending_repo.upsert(
        invitation_id=invitation_id,
        organization_id=organization_id,
        recipient_phone_e164=recipient_phone_e164,
        recipient_email=recipient_email,
    )
    if recipient_user_id is None:
        return False
    memberships = await projections.memberships_for_user(recipient_user_id)
    member_row = next(
        (row for row in memberships if row.organization_id == organization_id), None
    )
    if member_row is None:
        return False
    await fanout.notify_member(
        organization_id=organization_id,
        conversation_id=None,
        message_id=invitation_id,
        recipient_user_id=recipient_user_id,
        recipient_member_id=member_row.member_id,
        notification_type="INVITATION",
        sender_user_id=None,
        sender_label="Workspace",
        is_group=False,
        dedupe_message_id=invitation_id,
    )
    await pending_repo.mark_fulfilled(invitation_id, recipient_user_id)
    return True


async def fulfill_pending_for_phone(
    fanout: NotificationFanout,
    pending_repo: PendingInvitationRepository,
    projections,
    *,
    organization_id: UUID | None,
    phone_e164: str,
    user_id: UUID,
) -> int:
    delivered = 0
    pending_rows = (
        await pending_repo.pending_for_phone(organization_id, phone_e164)
        if organization_id is not None
        else await pending_repo.pending_for_phone_any_org(phone_e164)
    )
    for pending in pending_rows:
        organization_id = pending.organization_id
        membership = await projections.memberships_for_user(user_id)
        member_row = next(
            (row for row in membership if row.organization_id == pending.organization_id), None
        )
        if member_row is None or member_row.status not in {"ACTIVE", "INVITED"}:
            continue
        await fanout.notify_member(
            organization_id=pending.organization_id,
            conversation_id=None,
            message_id=pending.invitation_id,
            recipient_user_id=user_id,
            recipient_member_id=member_row.member_id,
            notification_type="INVITATION",
            sender_user_id=None,
            sender_label="Workspace",
            is_group=False,
            dedupe_message_id=pending.invitation_id,
        )
        await pending_repo.mark_fulfilled(pending.invitation_id, user_id)
        delivered += 1
    return delivered
