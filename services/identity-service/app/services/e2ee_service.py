import base64
import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.models import Device, DeviceE2eeBundle, DeviceOneTimePreKey, DeviceStatus
from app.schemas.e2ee import DeviceKeysUpload, PreKeyReplenishRequest, _decode_b64


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _fingerprint(identity_key: bytes) -> str:
    return hashlib.sha256(identity_key).hexdigest()[:16]


class E2eeService:
    async def upsert_device_keys(
        self,
        db: AsyncSession,
        device: Device,
        payload: DeviceKeysUpload,
    ) -> DeviceE2eeBundle:
        if device.status != DeviceStatus.ACTIVE:
            raise DomainError("DEVICE_REVOKED", "Device is not active.", 403)
        identity_key = _decode_b64(payload.identity_key, 32, 33)
        signed = payload.signed_pre_key
        kyber = payload.kyber_pre_key
        row = await db.get(DeviceE2eeBundle, device.id)
        now = datetime.now(UTC)
        if row is None:
            row = DeviceE2eeBundle(
                device_id=device.id,
                identity_id=device.identity_id,
                registration_id=payload.registration_id,
                identity_key_public=identity_key,
                key_version=1,
                signed_prekey_id=signed["key_id"],
                signed_prekey_public=_decode_b64(signed["public_key"], 32, 64),
                signed_prekey_signature=_decode_b64(signed["signature"], 64, 128),
                kyber_prekey_id=kyber["key_id"],
                kyber_prekey_public=_decode_b64(kyber["public_key"], 100, 2048),
                kyber_prekey_signature=_decode_b64(kyber["signature"], 64, 128),
                created_at=now,
                rotated_at=now,
            )
            db.add(row)
        else:
            changed_identity = row.identity_key_public != identity_key
            row.registration_id = payload.registration_id
            row.identity_key_public = identity_key
            row.signed_prekey_id = signed["key_id"]
            row.signed_prekey_public = _decode_b64(signed["public_key"], 32, 64)
            row.signed_prekey_signature = _decode_b64(signed["signature"], 64, 128)
            row.kyber_prekey_id = kyber["key_id"]
            row.kyber_prekey_public = _decode_b64(kyber["public_key"], 100, 2048)
            row.kyber_prekey_signature = _decode_b64(kyber["signature"], 64, 128)
            row.rotated_at = now
            if changed_identity:
                row.key_version += 1
        await self._store_prekeys(db, device.id, payload.one_time_pre_keys)
        await db.flush()
        return row

    async def replenish(
        self,
        db: AsyncSession,
        device: Device,
        payload: PreKeyReplenishRequest,
    ) -> int:
        if device.status != DeviceStatus.ACTIVE:
            raise DomainError("DEVICE_REVOKED", "Device is not active.", 403)
        await self._store_prekeys(db, device.id, payload.one_time_pre_keys)
        await db.flush()
        return len(payload.one_time_pre_keys)

    async def _store_prekeys(self, db, device_id: UUID, items) -> None:
        for item in items:
            existing = await db.scalar(
                select(DeviceOneTimePreKey).where(
                    DeviceOneTimePreKey.device_id == device_id,
                    DeviceOneTimePreKey.prekey_id == item.pre_key_id,
                    DeviceOneTimePreKey.consumed_at.is_(None),
                )
            )
            if existing:
                continue
            db.add(
                DeviceOneTimePreKey(
                    id=uuid4(),
                    device_id=device_id,
                    prekey_id=item.pre_key_id,
                    public_key=_decode_b64(item.public_key, 32, 64),
                )
            )

    async def list_identity_devices(
        self, db: AsyncSession, identity_id: UUID
    ) -> list[dict]:
        rows = (
            await db.execute(
                select(Device, DeviceE2eeBundle)
                .outerjoin(DeviceE2eeBundle, DeviceE2eeBundle.device_id == Device.id)
                .where(Device.identity_id == identity_id, Device.status == DeviceStatus.ACTIVE)
                .order_by(Device.last_seen_at.desc())
            )
        ).all()
        result = []
        for device, bundle in rows:
            entry = {
                "device_id": device.id,
                "platform": device.platform,
                "device_name": device.device_name,
                "status": device.status,
                "registration_id": bundle.registration_id if bundle else None,
                "key_version": bundle.key_version if bundle else None,
                "identity_key_fingerprint": _fingerprint(bundle.identity_key_public)
                if bundle
                else None,
                "rotated_at": bundle.rotated_at if bundle else None,
            }
            result.append(entry)
        return result

    async def fetch_prekey_bundle(
        self,
        db: AsyncSession,
        identity_id: UUID,
        device_id: UUID,
    ) -> dict:
        device = await db.scalar(
            select(Device).where(Device.id == device_id, Device.identity_id == identity_id)
        )
        if device is None or device.status != DeviceStatus.ACTIVE:
            raise DomainError("DEVICE_NOT_FOUND", "Device was not found.", 404)
        bundle = await db.get(DeviceE2eeBundle, device_id)
        if bundle is None:
            raise DomainError("E2EE_NOT_CONFIGURED", "Device has no published keys.", 404)
        prekey = await db.scalar(
            select(DeviceOneTimePreKey)
            .where(
                DeviceOneTimePreKey.device_id == device_id,
                DeviceOneTimePreKey.consumed_at.is_(None),
            )
            .order_by(DeviceOneTimePreKey.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        one_time = None
        if prekey is not None:
            prekey.consumed_at = datetime.now(UTC)
            one_time = {
                "pre_key_id": prekey.prekey_id,
                "public_key": _b64(prekey.public_key),
            }
        return {
            "registration_id": bundle.registration_id,
            "device_id": device_id,
            "identity_id": identity_id,
            "key_version": bundle.key_version,
            "identity_key": _b64(bundle.identity_key_public),
            "signed_pre_key": {
                "key_id": bundle.signed_prekey_id,
                "public_key": _b64(bundle.signed_prekey_public),
                "signature": _b64(bundle.signed_prekey_signature),
            },
            "kyber_pre_key": {
                "key_id": bundle.kyber_prekey_id,
                "public_key": _b64(bundle.kyber_prekey_public),
                "signature": _b64(bundle.kyber_prekey_signature),
            },
            "one_time_pre_key": one_time,
        }

    async def purge_device(self, db: AsyncSession, device_id: UUID) -> None:
        await db.execute(delete(DeviceOneTimePreKey).where(DeviceOneTimePreKey.device_id == device_id))
        await db.execute(delete(DeviceE2eeBundle).where(DeviceE2eeBundle.device_id == device_id))
