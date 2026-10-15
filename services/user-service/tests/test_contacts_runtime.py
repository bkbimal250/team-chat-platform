import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from redis.asyncio import Redis

from app.contacts_runtime import identity_lookup, rate_limit


def test_real_redis_atomic_identity_ip_limits_ttl_and_cleanup():
    async def run():
        redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        a, b, c = uuid4(), uuid4(), uuid4()
        ip = "contact-test-" + str(uuid4())
        request = SimpleNamespace(
            client=SimpleNamespace(host=ip),
            app=SimpleNamespace(state=SimpleNamespace(contact_redis=redis)),
        )
        keys = [
            f"contacts:{kind}:{scope}:{value}"
            for kind in ("requests", "numbers")
            for scope, value in [("identity", a), ("identity", b), ("identity", c), ("ip", ip)]
        ]
        try:
            await rate_limit(request, a, 50)
            assert 0 < await redis.ttl(f"contacts:numbers:identity:{a}") <= 3600
            assert 0 < await redis.ttl(f"contacts:requests:identity:{a}") <= 60
            with pytest.raises(HTTPException) as error:
                await rate_limit(request, a, 1)
            assert error.value.status_code == 429 and int(error.value.headers["Retry-After"]) > 0
            await rate_limit(request, b, 50)
            with pytest.raises(HTTPException) as error:
                await rate_limit(request, c, 1)
            assert error.value.status_code == 429
            assert await redis.get(f"contacts:numbers:identity:{c}") is None
        finally:
            await redis.delete(*keys)
            await redis.aclose()

    asyncio.run(run())


def test_redis_failure_is_closed_and_sanitized():
    async def run():
        request = SimpleNamespace(
            client=SimpleNamespace(host="127.0.0.1"),
            app=SimpleNamespace(
                state=SimpleNamespace(
                    contact_redis=SimpleNamespace(
                        eval=AsyncMock(side_effect=RuntimeError("private connection details"))
                    )
                )
            ),
        )
        with pytest.raises(HTTPException) as error:
            await rate_limit(request, uuid4(), 1)
        assert error.value.status_code == 503 and "private" not in error.value.detail

    asyncio.run(run())


@pytest.mark.parametrize("status,expected", [(401, 503), (503, 503), (422, 422)])
def test_identity_boundary_failures_hide_sensitive_body(monkeypatch, status, expected, caplog):
    async def run():
        secret = "never-log-internal-test-token"
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", secret)
        phone = "+12025550123"

        async def handler(request):
            assert request.headers["X-Internal-Service-Token"] == secret
            return httpx.Response(status, json={"detail": "private upstream response " + phone})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            request = SimpleNamespace(
                app=SimpleNamespace(state=SimpleNamespace(contact_http=client))
            )
            with pytest.raises(HTTPException) as error:
                await identity_lookup(request, {"phones": [{"phone": phone}]})
            assert error.value.status_code == expected
            assert phone not in error.value.detail and "private upstream" not in error.value.detail
        assert secret not in caplog.text and phone not in caplog.text

    asyncio.run(run())
