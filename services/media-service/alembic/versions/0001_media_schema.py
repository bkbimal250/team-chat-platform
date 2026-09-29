"""media service initial schema

Revision ID: 0001_media_schema
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_media_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    status = postgresql.ENUM(
        "PENDING",
        "UPLOADING",
        "UPLOADED",
        "READY",
        "FAILED",
        "DELETING",
        "DELETED",
        name="mediastatus",
        create_type=False,
    )
    status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploader_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploader_member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploader_device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_type", sa.String(16), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("safe_filename", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("bucket", sa.String(255), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=False, unique=True),
        sa.Column("thumbnail_object_key", sa.String(1024)),
        sa.Column("status", status, nullable=False),
        sa.Column("upload_strategy", sa.String(16), nullable=False),
        sa.Column("multipart_upload_id", sa.String(255)),
        sa.Column("part_size_bytes", sa.BigInteger()),
        sa.Column("multipart_started_at", sa.DateTime(timezone=True)),
        sa.Column("multipart_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_media_org_conversation", "media", ["organization_id", "conversation_id"])
    op.create_index(
        "ix_media_org_uploader_status", "media", ["organization_id", "uploader_user_id", "status"]
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", sa.String(), nullable=False),
        sa.Column("correlation_id", sa.String(128), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "media_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("media_id", "message_id", name="uq_media_message_reference"),
    )
    op.create_table(
        "organization_storage_usage",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stored_bytes", sa.BigInteger(), nullable=False),
        sa.Column("media_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("organization_storage_usage")
    op.drop_table("media_references")
    op.drop_table("processed_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_media_org_uploader_status", table_name="media")
    op.drop_index("ix_media_org_conversation", table_name="media")
    op.drop_table("media")
    sa.Enum(name="mediastatus").drop(op.get_bind(), checkfirst=True)
