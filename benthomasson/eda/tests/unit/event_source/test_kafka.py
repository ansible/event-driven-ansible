import pytest
import asyncio
from unittest.mock import patch, MagicMock
from asyncmock import AsyncMock
from plugins.event_source.kafka import main as kafka_main


class MockQueue:
    def __init__(self):
        self.queue = []

    async def put(self, event):
        self.queue.append(event)


@pytest.fixture
def myqueue():
    return MockQueue()


class AsyncIterator:
    def __init__(self):
        self.count = 0

    async def __anext__(self):
        if self.count < 2:
            mock = MagicMock()
            mock.value = f"{{\"i\": {self.count}}}"
            self.count += 1
            return mock
        else:
            raise StopAsyncIteration


class MockConsumer(AsyncMock):
    def __aiter__(self):
        return AsyncIterator()


@pytest.mark.asyncio
def test_receive_from_kafka_place_in_queue(myqueue):
    with patch("plugins.event_source.kafka.AIOKafkaConsumer", new=MockConsumer):
        asyncio.run(kafka_main(myqueue, {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"}))
        assert myqueue.queue[0] == {"i": 0}
        assert len(myqueue.queue) == 2
