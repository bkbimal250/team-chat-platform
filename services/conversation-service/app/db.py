from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    str(settings().database_url),
    pool_size=settings().database_pool_size,
    max_overflow=settings().database_max_overflow,
    pool_pre_ping=True,
)
Sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def db():
    async with Sessions() as session:
        yield session
