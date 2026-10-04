"""Local operator recovery of already OTP-verified durable intents. No tokens or SMS."""

import argparse
import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.api.v1.registration import provision_registration
from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models.models import CompanyRegistration


async def recover(registration_id):
    settings = get_settings()
    url = make_url(str(settings.DATABASE_URL))
    if (
        settings.app_env != "development"
        or url.host not in {"localhost", "127.0.0.1"}
        or url.port != 5434
    ):
        raise RuntimeError("Recovery command is restricted to isolated local development.")
    async with SessionLocal.begin() as db:
        row = await db.scalar(
            select(CompanyRegistration)
            .where(CompanyRegistration.id == registration_id)
            .with_for_update()
        )
        if row is None or row.state not in {"VERIFIED", "COMPLETED"}:
            raise RuntimeError("Only an already verified registration can be recovered.")
        if row.state == "COMPLETED":
            return
        await provision_registration(db, row, "local-registration-recovery", "local-operator")
        row.state, row.last_error, row.verified_code_hash = "COMPLETED", None, None
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registration_id", type=UUID)
    args = parser.parse_args()
    asyncio.run(recover(args.registration_id))
    print("Verified company recovered; sign in using normal phone OTP.")
