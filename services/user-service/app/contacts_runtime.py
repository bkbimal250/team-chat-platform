from contextlib import asynccontextmanager

import httpx
from fastapi import HTTPException
from redis.asyncio import Redis

from app.config import get_settings


@asynccontextmanager
async def lifespan(app):
    app.state.contact_http = httpx.AsyncClient(timeout=5, trust_env=False, follow_redirects=False)
    app.state.contact_redis = Redis.from_url(str(get_settings().REDIS_URL), decode_responses=True)
    try:
        yield
    finally:
        await app.state.contact_http.aclose()
        await app.state.contact_redis.aclose()


async def identity_lookup(request, body):
    settings = get_settings()
    token = settings.INTERNAL_SERVICE_TOKEN
    if not token:
        raise HTTPException(503, "Contact discovery is unavailable.")
    try:
        response = await request.app.state.contact_http.post(
            settings.IDENTITY_SERVICE_URL.rstrip("/") + "/internal/v1/contact-discovery",
            json=body,
            headers={"X-Internal-Service-Token": token},
        )
        if response.status_code == 422:
            raise HTTPException(422, "Enter a valid complete phone number and country.")
        response.raise_for_status()
        return response.json()["results"]
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(503, "Contact discovery is unavailable.") from None


LIMIT_SCRIPT = """
for i,key in ipairs(KEYS) do
 if tonumber(redis.call('GET',key) or '0') + tonumber(ARGV[(i-1)*3+1]) > tonumber(ARGV[(i-1)*3+2]) then return math.max(1,redis.call('TTL',key)) end
end
for i,key in ipairs(KEYS) do
 local value=redis.call('INCRBY',key,ARGV[(i-1)*3+1])
 if value==tonumber(ARGV[(i-1)*3+1]) then redis.call('EXPIRE',key,ARGV[(i-1)*3+3]) end
end
return 0
"""


async def rate_limit(request, identity_id, count=0):
    ip = request.client.host if request.client else "unknown"
    keys = [f"contacts:requests:identity:{identity_id}", f"contacts:requests:ip:{ip}"]
    args = [1, 60, 60, 1, 120, 60]
    if count:
        keys += [f"contacts:numbers:identity:{identity_id}", f"contacts:numbers:ip:{ip}"]
        args += [count, 50, 3600, count, 100, 3600]
    try:
        retry = await request.app.state.contact_redis.eval(LIMIT_SCRIPT, len(keys), *keys, *args)
    except Exception:
        raise HTTPException(503, "Contact discovery is unavailable.") from None
    if retry:
        raise HTTPException(
            429,
            "Too many contact checks. Please try again later.",
            headers={"Retry-After": str(retry)},
        )
