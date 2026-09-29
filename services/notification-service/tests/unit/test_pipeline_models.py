from app.models import Base


def test_pipeline_tables_and_constraints_are_registered():
    tables = Base.metadata.tables
    expected = {
        "notifications",
        "notification_deliveries",
        "user_projections",
        "membership_projections",
        "conversation_projections",
        "conversation_member_projections",
        "processed_events",
        "outbox_events",
    }
    assert expected <= set(tables)
    assert any(
        constraint.name == "uq_notification_message_recipient"
        for constraint in tables["notifications"].constraints
    )
    assert any(
        constraint.name == "uq_delivery_notification_token"
        for constraint in tables["notification_deliveries"].constraints
    )
    assert tables["outbox_events"].c.payload.type.__class__.__name__ == "JSON"


def test_pipeline_migration_revision_exists():
    source = open("alembic/versions/0002_notification_pipeline.py", encoding="utf-8").read()
    assert 'down_revision = "0001_initial"' in source
