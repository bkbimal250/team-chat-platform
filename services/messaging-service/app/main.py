from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DomainError
from app.db import SessionLocal, get_session
from app.models import Message, MessageReaction
from app.schemas import EditMessage, ReactionInput, SendMessage, SequenceInput
from app.security import Principal, principal
from app.services import authorize, event, mark, send

app = FastAPI(title="messaging-service")


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.exception_handler(DomainError)
async def errors(_, e):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=e.status, content={"error": {"code": e.code, "message": e.message}}
    )


@app.post("/api/v1/conversations/{conversation_id}/messages")
async def create(
    conversation_id: UUID,
    body: SendMessage,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await send(db, p, conversation_id, body, request.headers.get("X-Correlation-ID", ""))


@app.get("/api/v1/conversations/{conversation_id}/messages")
async def history(
    conversation_id: UUID,
    before_sequence: int | None = None,
    after_sequence: int | None = None,
    limit: int = 50,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    await authorize(db, p, conversation_id)
    q = (
        select(Message)
        .where(
            Message.organization_id == p.organization_id, Message.conversation_id == conversation_id
        )
        .order_by(Message.sequence)
        .limit(min(limit, 100))
    )
    if before_sequence:
        q = q.where(Message.sequence < before_sequence)
    if after_sequence:
        q = q.where(Message.sequence > after_sequence)
    return list((await db.scalars(q)).all())


@app.patch("/api/v1/messages/{message_id}")
async def edit(
    message_id: UUID,
    body: EditMessage,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        m = await db.scalar(
            select(Message)
            .where(Message.id == message_id, Message.organization_id == p.organization_id)
            .with_for_update()
        )
        if not m or m.sender_member_id != p.member_id or m.type != "TEXT" or m.deleted_at:
            raise DomainError("MESSAGE_EDIT_FORBIDDEN", "Message cannot be edited.", 403)
        m.text = body.text
        m.edited_at = datetime.now(UTC)
        db.add(event(m, "message.edited.v1", request.headers.get("X-Correlation-ID", "")))
        return m


@app.delete("/api/v1/messages/{message_id}")
async def delete(
    message_id: UUID,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        m = await db.scalar(
            select(Message)
            .where(Message.id == message_id, Message.organization_id == p.organization_id)
            .with_for_update()
        )
        if not m or m.sender_member_id != p.member_id:
            raise DomainError("MESSAGE_DELETE_FORBIDDEN", "Message cannot be deleted.", 403)
        m.deleted_at = datetime.now(UTC)
        m.status = "DELETED"
        m.text = None
        db.add(event(m, "message.deleted.v1", request.headers.get("X-Correlation-ID", "")))
        return {"status": "DELETED"}


@app.post("/api/v1/messages/{message_id}/reactions")
async def add_reaction(
    message_id: UUID,
    body: ReactionInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        message = await db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.organization_id == p.organization_id,
                Message.deleted_at.is_(None),
            )
        )
        if not message:
            raise DomainError("MESSAGE_NOT_FOUND", "Message is unavailable.", 404)
        await authorize(db, p, message.conversation_id)
        row = await db.scalar(
            select(MessageReaction).where(
                MessageReaction.message_id == message_id,
                MessageReaction.member_id == p.member_id,
                MessageReaction.reaction == body.reaction,
            )
        )
        if row:
            return row
        row = MessageReaction(
            message_id=message_id,
            organization_id=p.organization_id,
            user_id=p.user_id,
            member_id=p.member_id,
            reaction=body.reaction,
        )
        db.add(row)
        db.add(
            event(message, "message.reaction_added.v1", request.headers.get("X-Correlation-ID", ""))
        )
        return row


@app.delete("/api/v1/messages/{message_id}/reactions/{reaction}")
async def remove_reaction(
    message_id: UUID,
    reaction: str,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        message = await db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.organization_id == p.organization_id,
                Message.deleted_at.is_(None),
            )
        )
        if not message:
            raise DomainError("MESSAGE_NOT_FOUND", "Message is unavailable.", 404)
        await authorize(db, p, message.conversation_id)
        row = await db.scalar(
            select(MessageReaction).where(
                MessageReaction.message_id == message_id,
                MessageReaction.member_id == p.member_id,
                MessageReaction.reaction == reaction,
            )
        )
        if row:
            await db.delete(row)
            db.add(
                event(
                    message,
                    "message.reaction_removed.v1",
                    request.headers.get("X-Correlation-ID", ""),
                )
            )
        return {"status": "REMOVED"}


@app.post("/api/v1/conversations/{conversation_id}/delivered")
async def delivered(
    conversation_id: UUID,
    body: SequenceInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await mark(
            db,
            p,
            conversation_id,
            body.sequence,
            False,
            request.headers.get("X-Correlation-ID", ""),
        )


@app.post("/api/v1/conversations/{conversation_id}/read")
async def read(
    conversation_id: UUID,
    body: SequenceInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await mark(
            db, p, conversation_id, body.sequence, True, request.headers.get("X-Correlation-ID", "")
        )
