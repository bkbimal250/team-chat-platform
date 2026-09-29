import asyncio
from uuid import uuid4

import pytest

from app.rabbit import OutboxPublisher, consume_delivery


class Channel:
    def __init__(self):
        self.acks = 0
        self.nacks = 0

    def basic_ack(self, _):
        self.acks += 1

    def basic_nack(self, _, requeue):
        self.nacks += int(requeue)


class Repository:
    def __init__(self, fail=False):
        self.fail = fail
        self.seen = set()

    async def process_event(self, event, apply):
        if self.fail:
            raise RuntimeError("rollback")
        if event["event_id"] in self.seen:
            return False
        self.seen.add(event["event_id"])
        await apply(None)
        return True


@pytest.mark.asyncio
async def test_rabbit_acks_only_after_successful_transaction_and_dedupes():
    channel, repository, calls = Channel(), Repository(), []
    event = f'{{"event_id":"{uuid4()}"}}'.encode()

    async def handler(_, __):
        calls.append("committed")

    await consume_delivery(repository, handler, channel, 1, event)
    await consume_delivery(repository, handler, channel, 2, event)
    assert channel.acks == 2 and channel.nacks == 0 and calls == ["committed"]


@pytest.mark.asyncio
async def test_rabbit_nacks_failure_and_cancellation_without_ack():
    channel = Channel()

    async def handler(_, __):
        raise RuntimeError("db")

    await consume_delivery(
        Repository(), handler, channel, 1, f'{{"event_id":"{uuid4()}"}}'.encode()
    )
    assert channel.acks == 0 and channel.nacks == 1

    async def cancelled(_, __):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await consume_delivery(
            Repository(), cancelled, channel, 2, f'{{"event_id":"{uuid4()}"}}'.encode()
        )
    assert channel.acks == 0 and channel.nacks == 2


@pytest.mark.asyncio
async def test_outbox_confirms_before_marking_published_and_retries():
    class Event:
        status = "PENDING"

    class Repo:
        def __init__(self):
            self.event = Event()
            self.session = self

        async def pending_outbox(self):
            return [self.event]

        async def commit(self):
            pass

    repo = Repo()

    async def no_confirm(_):
        return False

    await OutboxPublisher(repo, no_confirm).publish_pending()
    assert repo.event.status == "PENDING"

    async def confirm(_):
        return True

    await OutboxPublisher(repo, confirm).publish_pending()
    assert repo.event.status == "PUBLISHED"
