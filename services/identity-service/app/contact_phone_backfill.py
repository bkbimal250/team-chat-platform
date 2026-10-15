"""Idempotent exact-match index population. Never prints phones or digests."""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models.models import Identity
from app.security.contact_phone import phone_digest


async def run():
    secret = get_settings().CONTACT_MATCHING_SECRET
    if not secret:
        raise RuntimeError("CONTACT_MATCHING_SECRET is required")
    count = 0
    async with SessionLocal() as session:
        while True:
            rows = (
                await session.scalars(
                    select(Identity)
                    .where(
                        Identity.phone_number.is_not(None), Identity.contact_phone_digest.is_(None)
                    )
                    .limit(200)
                    .with_for_update()
                )
            ).all()
            if not rows:
                break
            for row in rows:
                row.contact_phone_digest = phone_digest(row.phone_number, secret)
            await session.commit()
            count += len(rows)
    await engine.dispose()
    print(f"Contact phone index populated: {count} rows.")


if __name__ == "__main__":
    asyncio.run(run())
