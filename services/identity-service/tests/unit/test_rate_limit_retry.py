from unittest.mock import AsyncMock

import pytest

from app.core.errors import DomainError
from app.services.rate_limit import RateLimiter


@pytest.mark.asyncio
@pytest.mark.parametrize("cooldown", [False, True])
async def test_rate_limit_reports_actual_ttl_without_relaxing_limits(cooldown):
    redis = AsyncMock()
    redis.incr.return_value = 11
    redis.set.return_value = False
    redis.ttl.return_value = 123
    limiter = RateLimiter(redis)
    with pytest.raises(DomainError) as error:
        if cooldown:
            await limiter.cooldown("private-key", 60)
        else:
            await limiter.hit("private-key", 10, 3600)
    assert error.value.status_code == 429
    assert error.value.details == {"retry_after": 123}
    assert "private-key" not in error.value.message
    redis.ttl.assert_awaited_once_with("private-key")
