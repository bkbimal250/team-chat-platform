"""Explicit trusted operator CLI; no public self-grant endpoint or automatic promotion."""

import argparse
import asyncio
import getpass
import os
import re
import sys
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select, text

from app.db.session import SessionLocal, engine
from app.models.models import (
    Identity,
    IdentityStatus,
    MembershipProjection,
    PlatformAudit,
    PlatformGrant,
)
from app.security.hashing import hash_secret


def normalized_email(value: str) -> str:
    local_value = value.strip().lower()
    try:
        return validate_email(
            local_value, check_deliverability=False, test_environment=True
        ).normalized.lower()
    except EmailNotValidError as exc:
        if os.getenv("APP_ENV") == "development" and re.fullmatch(
            r"[^@\s]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\.local", local_value
        ):
            return local_value
        raise ValueError("A valid email address is required") from exc


async def set_grant(db, identity_id: UUID, role: str | None, actor: str) -> None:
    """Apply an audited grant while the caller holds the platform advisory lock."""
    identity = await db.get(Identity, identity_id)
    if not identity or identity.status != IdentityStatus.ACTIVE:
        raise ValueError("An existing active Identity account is required")
    grants = (await db.scalars(select(PlatformGrant).with_for_update())).all()
    current = next((row for row in grants if row.identity_id == identity_id), None)
    other_super = any(
        row.active and row.role == "SUPER_ADMIN" and row.identity_id != identity_id
        for row in grants
    )
    if (
        current
        and current.active
        and current.role == "SUPER_ADMIN"
        and role != "SUPER_ADMIN"
        and not other_super
    ):
        raise ValueError("Cannot remove the last active SUPER_ADMIN")
    if role is not None:
        if current is None:
            current = PlatformGrant(identity_id=identity_id, role=role)
            db.add(current)
        current.role, current.active = role, True
    elif current:
        current.active = False
    else:
        raise ValueError("No platform grant exists")
    db.add(
        PlatformAudit(
            actor=actor[:200],
            action=f"grant:{role}" if role else "revoke",
            target=identity_id,
            result="SUCCESS",
        )
    )


async def change(identity_id: UUID, role: str | None):
    async with SessionLocal() as db, db.begin():
        # Serialize grants/revocations including concurrent initial bootstrap.
        await db.execute(text("SELECT pg_advisory_xact_lock(70432191)"))
        await set_grant(db, identity_id, role, f"operator:{getpass.getuser()}")


async def bootstrap(email: str, display_name: str, password: str | None) -> None:
    """Create or ensure one local platform-only account without tenant membership."""
    email = normalized_email(email)
    async with SessionLocal() as db, db.begin():
        await db.execute(text("SELECT pg_advisory_xact_lock(70432191)"))
        identity = await db.scalar(
            select(Identity).where(Identity.email == email).with_for_update()
        )
        if identity is None:
            if password is None or not 12 <= len(password) <= 128:
                raise ValueError("A 12-128 character password is required for a new account")
            identity = Identity(
                email=email,
                password_hash=hash_secret(password),
                status=IdentityStatus.ACTIVE,
                email_verified=False,
                phone_verified=False,
            )
            db.add(identity)
            await db.flush()
        elif not identity.password_hash or identity.status != IdentityStatus.ACTIVE:
            raise ValueError("Existing account cannot be used for platform bootstrap")

        membership = await db.scalar(
            select(MembershipProjection.id)
            .where(MembershipProjection.identity_id == identity.id)
            .limit(1)
        )
        if membership is not None:
            raise ValueError("A workspace member cannot be converted into a platform-only account")
        await set_grant(db, identity.id, "SUPER_ADMIN", f"bootstrap:{display_name}")


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    grant = subcommands.add_parser("grant", help="grant or revoke an existing account")
    grant.add_argument("identity_id", type=UUID)
    grant.add_argument("action", choices=["SUPER_ADMIN", "ADMIN", "revoke"])
    local = subcommands.add_parser(
        "bootstrap", help="create or ensure a local platform-only super admin"
    )
    local.add_argument("--email", required=True)
    local.add_argument("--name", required=True)
    local.add_argument(
        "--password-env",
        help="environment variable containing a new-account password; never pass a password as an argument",
    )
    # Retain the original trusted-operator invocation documented for C1.
    legacy_grant = len(sys.argv) == 3 and sys.argv[1] not in {"grant", "bootstrap"}
    args = parser.parse_args(["grant", *sys.argv[1:]] if legacy_grant else None)
    try:
        if args.command == "grant":
            await change(args.identity_id, None if args.action == "revoke" else args.action)
            print("Platform authorization updated; operator action audited.")
        else:
            password = os.environ.get(args.password_env) if args.password_env else None
            if password is None and not args.password_env:
                password = (
                    getpass.getpass("New-account password (leave blank when rerunning): ") or None
                )
            await bootstrap(args.email, args.name, password)
            print("Local platform super admin ensured; no tenant membership was created.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
