from redis.asyncio import Redis

from app.core.errors import DomainError


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def hit(self, key: str, limit: int, window: int) -> None:
        value = await self.redis.incr(key)
        if value == 1:
            await self.redis.expire(key, window)
        if value > limit:
            raise DomainError("RATE_LIMITED", "Please try again later.", 429)

    async def cooldown(self, key: str, ttl: int) -> None:
        if not await self.redis.set(key, "1", ex=ttl, nx=True):
            raise DomainError(
                "OTP_RESEND_COOLDOWN", "Please wait before requesting another code.", 429
            )
