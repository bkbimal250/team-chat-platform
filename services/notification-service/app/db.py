import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
DATABASE_URL = os.environ.get(
    "NOTIFICATION_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql+asyncpg://localhost/teamchat_notification_db"),
)
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    async with SessionLocal() as session:
        yield session
