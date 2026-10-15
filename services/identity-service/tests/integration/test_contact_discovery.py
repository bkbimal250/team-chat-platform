from uuid import UUID

import pytest

from app.core.config import get_settings
from app.models.models import Identity

from .test_email_password import harness as harness
from .test_personal_accounts import personal_body


@pytest.mark.asyncio
async def test_internal_exact_index_active_only_and_phone_change(harness, monkeypatch, caplog):
    client, factory, _ = harness
    monkeypatch.setattr(
        get_settings(), "CONTACT_MATCHING_SECRET", "dedicated-test-key-not-production-" * 2
    )
    data = personal_body()
    replacement_phone = personal_body()["phone"]
    registered = await client.post("/api/v1/auth/registration/personal", json=data)
    assert registered.status_code == 201
    headers = {"X-Internal-Service-Token": get_settings().SERVICE_AUTH_TOKEN}
    body = {"phones": [{"phone": data["phone"]}]}
    assert (await client.post("/internal/v1/contact-discovery", json=body)).status_code == 401
    found = (
        await client.post("/internal/v1/contact-discovery", headers=headers, json=body)
    ).json()["results"][0]
    assert found["identity_id"] and found["phone_verified"] is False
    assert len(found["digest"]) == 64
    async with factory.begin() as s:
        identity = await s.get(Identity, UUID(found["identity_id"]))
        assert identity.contact_phone_digest == found["digest"]
        identity.phone_number = replacement_phone
    assert (await client.post("/internal/v1/contact-discovery", headers=headers, json=body)).json()[
        "results"
    ][0]["identity_id"] is None
    replacement = {"phones": [{"phone": replacement_phone}]}
    assert (
        await client.post("/internal/v1/contact-discovery", headers=headers, json=replacement)
    ).json()["results"][0]["identity_id"] == found["identity_id"]
    async with factory.begin() as s:
        identity = await s.get(Identity, UUID(found["identity_id"]))
        identity.status = "DISABLED"
    assert (
        await client.post("/internal/v1/contact-discovery", headers=headers, json=replacement)
    ).json()["results"][0]["identity_id"] is None
    assert data["phone"] not in caplog.text
    assert get_settings().CONTACT_MATCHING_SECRET not in caplog.text
    assert (
        await client.post(
            "/internal/v1/contact-discovery",
            headers=headers,
            json={"phones": [{"phone": data["phone"]}] * 21},
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_discovery_missing_secret_fails_closed(harness, monkeypatch):
    client, _, _ = harness
    monkeypatch.setattr(get_settings(), "CONTACT_MATCHING_SECRET", None)
    response = await client.post(
        "/internal/v1/contact-discovery",
        headers={"X-Internal-Service-Token": get_settings().SERVICE_AUTH_TOKEN},
        json={"phones": [{"phone": "+12025550123"}]},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_canonical_digest_constraint_prevents_formatted_duplicate(harness, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    client, factory, _ = harness
    monkeypatch.setattr(
        get_settings(), "CONTACT_MATCHING_SECRET", "canonical-uniqueness-test-key-" * 2
    )
    phone = personal_body()["phone"]
    async with factory.begin() as s:
        s.add(Identity(phone_number=phone, status="ACTIVE"))
    async with factory() as s:
        s.add(Identity(phone_number=phone[:3] + " " + phone[3:], status="ACTIVE"))
        with pytest.raises(IntegrityError):
            await s.commit()
        await s.rollback()
