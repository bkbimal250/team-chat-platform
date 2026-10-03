import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.chat_projection import summaries
from app.db import Base
from app.events import consume
from app.models import Conversation, ConversationMessageProjection


@compiles(JSONB, "sqlite")
def json_for_test(_, __, **kwargs):
    return "JSON"


@pytest.mark.asyncio
async def test_durable_summary_read_dedupe_tenant_and_out_of_order(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'summary.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    org, other_org, cid, member, sender = [uuid.uuid4() for _ in range(5)]
    async with sessions.begin() as db:
        db.add(
            Conversation(
                id=cid,
                organization_id=org,
                type="GROUP",
                created_by_member_id=member,
                status="ACTIVE",
            )
        )
    message_id = uuid.uuid4()
    timestamp = datetime.now(UTC).isoformat()
    event = dict(
        event_id=str(uuid.uuid4()),
        producer="messaging",
        organization_id=str(org),
        event_type="message.created.v1",
        occurred_at=timestamp,
        payload=dict(
            organization_id=str(org),
            conversation_id=str(cid),
            message_id=str(message_id),
            sender_member_id=str(sender),
            sequence=1,
            text="Real message",
            created_at=timestamp,
        ),
    )
    async with sessions.begin() as db:
        assert await consume(db, event)
    async with sessions.begin() as db:
        assert not await consume(db, event)
        result = await summaries(db, org, member, [cid])
        assert (
            result[cid]["last_message_preview"] == "Real message"
            and result[cid]["unread_count"] == 1
        )
        assert (await summaries(db, other_org, member, [cid]))[cid]["unread_count"] == 0
    async with sessions.begin() as db:
        read_event = event | {
            "event_id": str(uuid.uuid4()),
            "event_type": "message.read.v1",
            "payload": {"conversation_id": str(cid), "member_id": str(member), "sequence": 1},
        }
        await consume(db, read_event)
    # A new session reads durable data, not consumer process memory.
    async with sessions.begin() as db:
        assert (await summaries(db, org, member, [cid]))[cid]["unread_count"] == 0
        await consume(
            db, event | {"event_id": str(uuid.uuid4()), "event_type": "message.deleted.v1"}
        )
    async with sessions.begin() as db:
        await consume(db, event | {"event_id": str(uuid.uuid4())})
        assert (await db.get(ConversationMessageProjection, message_id)).is_deleted
        assert (await summaries(db, org, member, [cid]))[cid]["last_message_preview"] is None
        with pytest.raises(ValueError, match="tenant mismatch"):
            await consume(
                db, event | {"event_id": str(uuid.uuid4()), "organization_id": str(other_org)}
            )
    async with sessions.begin() as db:
        media_event = event | {
            "event_id": str(uuid.uuid4()),
            "payload": event["payload"]
            | {"message_id": str(uuid.uuid4()), "sequence": 2, "text": None, "type": "IMAGE"},
        }
        await consume(db, media_event)
    async with sessions.begin() as db:
        result = await summaries(db, org, member, [cid])
        assert result[cid]["last_message_preview"] == "Image"
        assert result[cid]["unread_count"] == 1
    await engine.dispose()


def test_summary_migration_adds_and_removes_only_projection_tables(tmp_path):
    import importlib.util
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    path = Path(__file__).parents[2] / "alembic" / "versions" / "0002_chat_summaries.py"
    spec = importlib.util.spec_from_file_location("summary_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    with engine.begin() as connection:
        legacy = [
            table
            for name, table in Base.metadata.tables.items()
            if name not in {"conversation_message_projections", "conversation_read_projections"}
        ]
        Base.metadata.create_all(connection, tables=legacy)
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert inspect(connection).has_table("conversation_message_projections")
        assert inspect(connection).has_table("conversation_read_projections")
        assert (
            inspect(connection).get_indexes("conversation_message_projections")[0]["name"]
            == "conversation_message_summary"
        )
        migration.upgrade()
        migration.downgrade()
        assert inspect(connection).has_table("conversations")
        assert not inspect(connection).has_table("conversation_message_projections")
    engine.dispose()
