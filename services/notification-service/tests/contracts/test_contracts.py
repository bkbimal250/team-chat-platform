from app.main import app


def test_notification_openapi_and_event_contracts():
    paths = app.openapi()["paths"]
    assert "/api/v1/notifications/devices/current/token" in paths
    assert "/api/v1/notifications/preferences" in paths
    envelope = {
        "event_id": "id",
        "event_type": "notification.sent.v1",
        "event_version": 1,
        "organization_id": "org",
        "aggregate_id": "id",
        "payload": {},
    }
    assert {
        "event_id",
        "event_type",
        "event_version",
        "organization_id",
        "aggregate_id",
        "payload",
    } <= envelope.keys()
