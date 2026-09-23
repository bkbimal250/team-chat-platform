import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core import settings
from app.db import Base


def migrate(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run():
    e = create_async_engine(str(settings().database_url))
    async with e.connect() as c:
        await c.run_sync(migrate)
    await e.dispose()


asyncio.run(run())
