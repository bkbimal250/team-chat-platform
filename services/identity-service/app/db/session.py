from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal, engine  # noqa: F401

# Alias used by health checks and other callers expecting a sessionmaker
SessionLocal = AsyncSessionLocal


# FastAPI dependency for request scoped sessions
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Backward-compatible dependency name used by the mounted API routers.
get_session = get_async_session
