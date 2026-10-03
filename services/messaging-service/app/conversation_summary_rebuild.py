"""Explicit operator backfill; no SMS, notifications, or realtime message replay.

After migrating Conversation and starting its updated consumer, an operator can
run: python -m app.conversation_summary_rebuild --stage
This only stages summary-specific outbox events; the existing publisher delivers
these to Conversation Service. No public per-conversation API calls are made.
"""

import argparse
import asyncio

from sqlalchemy import select

from app.db import SessionLocal
from app.models import ConversationReadState, Message, OutboxEvent
from app.services import event


def message_snapshot(message):
    kind = (
        "message.deleted.v1"
        if message.deleted_at
        else "message.edited.v1"
        if message.edited_at
        else "message.created.v1"
    )
    return event(message, "conversation.summary.message.v1", "summary-rebuild", source_kind=kind)


def read_snapshot(row):
    return OutboxEvent(
        event_type="conversation.summary.read.v1",
        aggregate_id=row.conversation_id,
        organization_id=row.organization_id,
        correlation_id="summary-rebuild",
        payload={
            "organization_id": str(row.organization_id),
            "conversation_id": str(row.conversation_id),
            "member_id": str(row.member_id),
            "sequence": row.last_read_sequence,
        },
    )


async def stage():
    count = 0
    for model, snapshot in ((Message, message_snapshot), (ConversationReadState, read_snapshot)):
        cursor = None
        while True:
            async with SessionLocal.begin() as db:
                query = select(model).order_by(model.id).limit(500)
                if cursor is not None:
                    query = query.where(model.id > cursor)
                rows = (await db.scalars(query)).all()
                if not rows:
                    break
                for row in rows:
                    db.add(snapshot(row))
                cursor = rows[-1].id
                count += len(rows)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage durable conversation summary backfill")
    parser.add_argument("--stage", action="store_true", required=True)
    parser.parse_args()
    print(f"Summary events staged: {asyncio.run(stage())}")
