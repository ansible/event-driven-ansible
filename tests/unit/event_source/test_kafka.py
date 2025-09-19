from __future__ import annotations

import asyncio
import json
import re
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


class MockConsumer(AsyncMock):  # type: ignore[misc]
    def __aiter__(self) -> AsyncIterator:
        return AsyncIterator()

    def subscribe(self, topics: list[str], pattern: str | None = None) -> None:
        assert topics or pattern
        assert not (topics and pattern)


@pytest.mark.parametrize(
    "topic_type, topic_value",
    [("topic", "eda"), ("topics", ["eda1", "eda2"]), ("topic_pattern", "eda_*")],
)
def test_receive_from_kafka_place_in_queue(
    myqueue: MockQueue, topic_type: str, topic_value: str | list[str]
) -> None:
    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer", new=MockConsumer
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    topic_type: topic_value,
                    "host": "localhost",
                    "port": 9092,
                    "group_id": "test",
                },
            )
        )
        assert myqueue.queue[0] == {
            "body": {"i": 0},
            "meta": {"headers": {"foo": "bar"}},
        }
        assert len(myqueue.queue) == 2


@pytest.mark.parametrize(
    "topic_args",
    [
        {"topic": "eda", "topics": ["eda1", "eda2"], "topic_pattern": "eda_*"},
        {"topics": ["eda1", "eda2"], "topic_pattern": "eda_*"},
        {"topic": "eda", "topic_pattern": "eda_*"},
        {"topic": "eda", "topics": ["eda1", "eda2"]},
    ],
)
def test_mixed_topics_and_patterns(
    myqueue: MockQueue, topic_args: dict[str, Any]
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one of topic, topics, or topic_pattern must be provided.",
    ):
        asyncio.run(kafka_main(myqueue, topic_args))


@pytest.mark.parametrize(
    "args, error_msg",
    [
        # Only host set
        (
            {"host": "localhost", "port": None, "brokers": None, "topic": "eda"},
            "Port and host must be set",
        ),
        # Only port set
        (
            {"host": None, "port": 9092, "brokers": None, "topic": "eda"},
            "Port and host must be set",
        ),
        # Neither host nor brokers set
        (
            {"host": None, "port": None, "brokers": None, "topic": "eda"},
            "host + port or brokers must be set",
        ),
        # Both host and brokers set
        (
            {
                "host": "localhost",
                "port": 9092,
                "brokers": ["localhost:9092"],
                "topic": "eda",
            },
            "Only one of host and brokers parameter must be set",
        ),
    ],
)
def test_host_port_brokers_combinations(
    myqueue: MockQueue, args: dict[str, Any], error_msg: str
) -> None:
    with pytest.raises(ValueError, match=re.escape(error_msg)):
        asyncio.run(kafka_main(myqueue, args))
