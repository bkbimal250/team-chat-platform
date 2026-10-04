"""Explicit local-only identities; never enables public self-registration."""

import asyncio
import os
from uuid import NAMESPACE_URL, uuid5

from app.db.session import SessionLocal, engine
from app.models.models import Identity, OutboxEvent
from sqlalchemy import select


async def main():
    if os.environ.get(
        "OTP_PROVIDER"
    ) != "development" or "127.0.0.1:5434/identity_db" not in os.environ.get(
        "DATABASE_URL", ""
    ):
        raise RuntimeError("Seed is restricted to isolated local development")
    async with SessionLocal.begin() as db:
        for number, name in [
            ("+919000000001", "Local Alice"),
            ("+919000000002", "Local Bob"),
        ]:
            identity_id = uuid5(NAMESPACE_URL, "globalchat-local:" + number)
            if await db.scalar(select(Identity.id).where(Identity.id == identity_id)):
                continue
            db.add(Identity(id=identity_id, phone_number=number, status="ACTIVE"))
            db.add(
                OutboxEvent(
                    event_type="identity.created.v1",
                    aggregate_type="identity",
                    aggregate_id=identity_id,
                    correlation_id="local-seed",
                    payload={
                        "identity_id": str(identity_id),
                        "resource_id": str(identity_id),
                        "display_name": name,
                        "status": "ACTIVE",
                    },
                )
            )
    await engine.dispose()
    print("Two explicit local identities ready")


asyncio.run(main())
