import hmac

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import Identity, IdentityStatus
from app.security.contact_phone import phone_digest
from app.security.phone import normalize_phone

router = APIRouter()


class PhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str = Field(min_length=3, max_length=64)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")


class Lookup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phones: list[PhoneInput] = Field(default_factory=list, max_length=20)
    digests: list[str] = Field(default_factory=list, max_length=50)


async def internal(token: str = Header("", alias="X-Internal-Service-Token")):
    if (
        not token
        or not get_settings().SERVICE_AUTH_TOKEN
        or not hmac.compare_digest(token, get_settings().SERVICE_AUTH_TOKEN)
    ):
        raise DomainError("UNAUTHORIZED", "Service authentication required.", 401)


@router.post(
    "/internal/v1/contact-discovery", dependencies=[Depends(internal)], include_in_schema=False
)
async def lookup(body: Lookup, session: AsyncSession = Depends(get_session)):
    secret = get_settings().CONTACT_MATCHING_SECRET
    if not secret:
        raise DomainError("CONTACT_DISCOVERY_UNAVAILABLE", "Contact discovery is unavailable.", 503)
    if bool(body.phones) == bool(body.digests):
        raise DomainError("VALIDATION_ERROR", "Supply one bounded lookup batch.", 422)
    digests = (
        [phone_digest(normalize_phone(p.phone, p.country), secret) for p in body.phones]
        if body.phones
        else body.digests
    )
    if any(len(d) != 64 or any(c not in "0123456789abcdef" for c in d) for d in digests):
        raise DomainError("VALIDATION_ERROR", "Invalid lookup batch.", 422)
    identities = (
        await session.scalars(
            select(Identity).where(
                Identity.contact_phone_digest.in_(set(digests)),
                Identity.status == IdentityStatus.ACTIVE,
                Identity.deleted_at.is_(None),
                Identity.disabled_at.is_(None),
            )
        )
    ).all()
    found = {i.contact_phone_digest: i for i in identities}
    return {
        "results": [
            {
                "digest": d,
                "identity_id": str(found[d].id) if d in found else None,
                "phone_verified": found[d].phone_verified if d in found else None,
            }
            for d in digests
        ]
    }
