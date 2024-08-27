import asyncio
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from asyncmock import AsyncMock

from extensions.eda.plugins.event_source.kafka import main as kafka_main


class MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, item: Any) -> None:
        self.queue.append(item)


@pytest.fixture
def myqueue() -> MockQueue:
    return MockQueue()


class AsyncIterator:
    def __init__(self) -> None:
        self.count = 0

    async def __anext__(self) -> MagicMock:
        if self.count < 2:
            mock = MagicMock()
            mock.value = f'{{"i": {self.count}}}'.encode("utf-8")
            mock.headers = [
                (key, value.encode("utf-8"))
                for key, value in json.loads('{"foo": "bar"}').items()
            ]
            self.count += 1
            return mock
        else:
            raise StopAsyncIteration


class MockConsumer(AsyncMock):
    def __aiter__(self) -> AsyncIterator:
        return AsyncIterator()


def test_receive_from_kafka_place_in_queue(myqueue: MockQueue) -> None:
    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer", new=MockConsumer
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                },
            )
        )
        assert myqueue.queue[0] == {
            "body": {"i": 0},
            "meta": {"headers": {"foo": "bar"}},
        }
        assert len(myqueue.queue) == 2
