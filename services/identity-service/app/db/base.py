from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Async engine with optional pool settings
engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_size=getattr(settings, "DATABASE_POOL_SIZE", 10),
    max_overflow=getattr(settings, "DATABASE_MAX_OVERFLOW", 10),
    future=True,
)

# Session maker for request‑scoped async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()
