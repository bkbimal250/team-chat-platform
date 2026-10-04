from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.session import command_transaction


@pytest.mark.asyncio
async def test_authenticated_transaction_is_committed_without_second_begin():
    session = MagicMock()
    session.in_transaction.return_value = True
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    async with command_transaction(session):
        pass
    session.begin.assert_not_called()
    session.commit.assert_awaited_once()
    session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_authenticated_transaction_rolls_back_on_failure():
    session = MagicMock()
    session.in_transaction.return_value = True
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    with pytest.raises(ValueError):
        async with command_transaction(session):
            raise ValueError("failed")
    session.rollback.assert_awaited_once()
    session.commit.assert_not_called()
