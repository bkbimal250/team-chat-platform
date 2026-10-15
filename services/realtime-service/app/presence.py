"""Identity presence with Redis TTL and authorized watch subscriptions."""

from uuid import UUID

import httpx

from app.auth import Principal
from app.core import ProtocolError, settings


class PresenceService:
    def __init__(self, redis=None, membership_store=None):
        self.redis = redis
        self.membership_store = membership_store

    def _presence_key(self, identity_id: UUID) -> str:
        return f"realtime:presence:{identity_id}"

    async def touch(self, principal: Principal, ttl: int = 90) -> None:
        if not self.redis:
            return
        key = self._presence_key(principal.identity_id)
        was_absent = not await self.redis.exists(key)
        device_field = str(principal.device_id)
        await self.redis.hset(key, device_field, "1")
        await self.redis.expire(key, ttl)
        if was_absent:
            await self._notify_watchers(principal.identity_id, True)

    async def clear(self, principal: Principal) -> None:
        if not self.redis:
            return
        key = self._presence_key(principal.identity_id)
        device_field = str(principal.device_id)
        await self.redis.hdel(key, device_field)
        remaining = await self.redis.hlen(key)
        if remaining == 0:
            await self.redis.delete(key)
            await self._notify_watchers(principal.identity_id, False)

    async def _notify_watchers(self, identity_id: UUID, online: bool) -> None:
        callback = getattr(self, "_notify_watchers_callback", None)
        if callback:
            await callback(identity_id, online)

    async def authorize_watch(self, watcher: Principal, target_id: UUID) -> None:
        if watcher.identity_id == target_id:
            return
        configured = settings()
        if not configured.user_service_url or not configured.internal_service_token:
            raise ProtocolError("PRESENCE_FORBIDDEN", "Presence is unavailable.")
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
                response = await client.post(
                    f"{configured.user_service_url.rstrip('/')}/internal/v1/contacts/presence-permission",
                    headers={"X-Internal-Service-Token": configured.internal_service_token},
                    json={
                        "identity_id": str(watcher.identity_id),
                        "target_identity_id": str(target_id),
                    },
                )
            if response.status_code not in {200, 404, 403}:
                response.raise_for_status()
            if response.status_code != 200 or response.json().get("allowed") is not True:
                raise ProtocolError("PRESENCE_FORBIDDEN", "Presence is unavailable.")
        except (httpx.HTTPError, ValueError, TypeError):
            raise ProtocolError("PRESENCE_FORBIDDEN", "Presence is unavailable.") from None

    async def snapshot(self, identity_id: UUID) -> dict:
        if not self.redis:
            return {"identity_id": str(identity_id), "online": False}
        online = bool(await self.redis.hlen(self._presence_key(identity_id)))
        return {
            "identity_id": str(identity_id),
            "online": online,
        }
