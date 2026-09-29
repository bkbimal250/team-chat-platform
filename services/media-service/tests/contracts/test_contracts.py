from uuid import uuid4

from app.main import app
from app.service import MediaService
from app.storage import FakePrivateStorage


def test_openapi_exposes_private_media_lifecycle_endpoints():
    paths = app.openapi()["paths"]
    assert "/api/v1/media/uploads" in paths
    assert "/api/v1/media/{media_id}/complete" in paths
    assert "/api/v1/media/{media_id}/download" in paths
    assert "/api/v1/media/multipart" in paths
    assert "/api/v1/media/{media_id}/multipart/parts" in paths
    assert "/api/v1/media/{media_id}/multipart/complete" in paths


def test_media_event_envelopes_follow_platform_contract():
    service = MediaService(FakePrivateStorage())
    media = type(
        "Media", (), {"organization_id": uuid4(), "id": uuid4(), "conversation_id": uuid4()}
    )()
    for event_type in ("media.ready.v1", "media.failed.v1", "media.deleted.v1"):
        service._event(event_type, media, "trace-1")
    assert all(
        {
            "event_id",
            "event_type",
            "event_version",
            "organization_id",
            "aggregate_id",
            "correlation_id",
            "payload",
        }
        <= event.keys()
        for event in service.outbox
    )
