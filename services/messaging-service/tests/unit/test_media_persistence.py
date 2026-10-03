import importlib.util
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.db import Base
from app.models import MediaProjection, Message


@compiles(JSONB, "sqlite")
def json_test_type(_, __, **kwargs):
    return "JSON"


def test_attachment_and_authorization_metadata_survive_new_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    org, cid, member, user, device, mid = [uuid4() for _ in range(6)]
    attachment = {
        "media_id": str(mid),
        "media_type": "image",
        "mime_type": "image/png",
        "filename": "image.png",
        "size_bytes": 100,
    }
    with Session(engine) as db:
        db.add(
            MediaProjection(
                id=mid,
                organization_id=org,
                conversation_id=cid,
                uploader_member_id=member,
                status="READY",
                metadata_json=attachment,
            )
        )
        message = Message(
            organization_id=org,
            conversation_id=cid,
            sender_member_id=member,
            sender_user_id=user,
            sender_device_id=device,
            type="IMAGE",
            text=None,
            attachment=attachment,
            client_message_id=uuid4(),
            sequence=1,
        )
        db.add(message)
        db.commit()
        message_id = message.id
    with Session(engine) as db:
        assert db.get(Message, message_id).attachment == attachment
        assert db.get(MediaProjection, mid).uploader_member_id == member
    engine.dispose()


def test_media_migration_preserves_existing_messages_and_downgrades():
    path = Path(__file__).parents[2] / "alembic" / "versions" / "0002_media_messages.py"
    spec = importlib.util.spec_from_file_location("media_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE messages (id TEXT PRIMARY KEY)"))
        connection.execute(text("INSERT INTO messages (id) VALUES ('existing')"))
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        migration.upgrade()
        assert inspect(connection).has_table("media_projections")
        assert connection.execute(text("SELECT id, attachment FROM messages")).one() == (
            "existing",
            None,
        )
        migration.downgrade()
        assert not inspect(connection).has_table("media_projections")
        assert connection.execute(text("SELECT id FROM messages")).scalar() == "existing"
    engine.dispose()
