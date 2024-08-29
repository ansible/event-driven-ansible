"""Tests for pg_listener source plugin"""

import asyncio
import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg
import pytest
import xxhash

from extensions.eda.plugins.event_source.pg_listener import (
    MESSAGE_CHUNK,
    MESSAGE_CHUNK_COUNT,
    MESSAGE_CHUNK_SEQUENCE,
    MESSAGE_CHUNKED_UUID,
    MESSAGE_LENGTH,
    MESSAGE_XX_HASH,
)
from extensions.eda.plugins.event_source.pg_listener import main as pg_listener_main

MAX_LENGTH = 7 * 1024


class _MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, event: Any) -> None:
        """Put an event into the queue"""
        self.queue.append(event)


class _AsyncIterator:
    def __init__(self, data: Any) -> None:
        self.count = 0
        self.data = data

    def __aiter__(self) -> "_AsyncIterator":
        return _AsyncIterator(self.data)

    async def __aenter__(self) -> "_AsyncIterator":
        return self

    async def __anext__(self) -> MagicMock:
        if self.count >= len(self.data):
            raise StopAsyncIteration

        mock = MagicMock()
        mock.payload = self.data[self.count]
        self.count += 1
        return mock


def _to_chunks(payload: str, result: list[str]) -> None:
    message_length = len(payload)
    if message_length >= MAX_LENGTH:
        xx_hash = xxhash.xxh32(payload.encode("utf-8")).hexdigest()
        message_uuid = str(uuid.uuid4())
        number_of_chunks = int(message_length / MAX_LENGTH) + 1
        chunked = {
            MESSAGE_CHUNKED_UUID: message_uuid,
            MESSAGE_CHUNK_COUNT: number_of_chunks,
            MESSAGE_LENGTH: message_length,
            MESSAGE_XX_HASH: xx_hash,
        }
        sequence = 1
        for i in range(0, message_length, MAX_LENGTH):
            chunked[MESSAGE_CHUNK] = payload[i : i + MAX_LENGTH]
            chunked[MESSAGE_CHUNK_SEQUENCE] = sequence
            sequence += 1
            result.append(json.dumps(chunked))
    else:
        result.append(payload)


TEST_PAYLOADS = [
    [{"a": 1, "b": 2}, {"name": "Fred", "kids": ["Pebbles"]}],
    [{"blob": "x" * 9000, "huge": "h" * 9000}],
    [{"a": 1, "x": 2}, {"x": "y" * 20000, "fail": False, "pi": 3.14159}],
]


@pytest.mark.parametrize("events", TEST_PAYLOADS)
def test_receive_from_pg_listener(events: list[dict[str, Any]]) -> None:
    """Test receiving different payloads from pg notify."""
    notify_payload: list[str] = []
    myqueue = _MockQueue()
    for event in events:
        _to_chunks(json.dumps(event), notify_payload)

    def my_iterator() -> _AsyncIterator:
        return _AsyncIterator(notify_payload)

    with patch(
        "extensions.eda.plugins.event_source.pg_listener.AsyncConnection.connect"
    ) as conn:
        mock_object = AsyncMock()
        conn.return_value = mock_object
        conn.return_value.__aenter__.return_value = mock_object
        mock_object.cursor = AsyncMock
        mock_object.notifies = my_iterator

        asyncio.run(
            pg_listener_main(
                myqueue,
                {
                    "dsn": "host=localhost dbname=mydb user=postgres password=password",
                    "channels": ["test"],
                },
            )
        )

        assert len(myqueue.queue) == len(events)
        index = 0
        for event in events:
            assert myqueue.queue[index] == event
            index += 1


def test_decoding_error() -> None:
    """Test json parsing error"""
    notify_payload: list[str] = ['{"a"; "b"}']
    myqueue = _MockQueue()

    def my_iterator() -> _AsyncIterator:
        return _AsyncIterator(notify_payload)

    with patch(
        "extensions.eda.plugins.event_source.pg_listener.AsyncConnection.connect"
    ) as conn:
        mock_object = AsyncMock()
        conn.return_value = mock_object
        conn.return_value.__aenter__.return_value = mock_object
        mock_object.cursor = AsyncMock
        mock_object.notifies = my_iterator

        with pytest.raises(json.decoder.JSONDecodeError):
            asyncio.run(
                pg_listener_main(
                    myqueue,
                    {
                        "dsn": (
                            "host=localhost dbname=mydb "
                            "user=postgres password=password"
                        ),
                        "channels": ["test"],
                    },
                )
            )


def test_operational_error() -> None:
    """Test json parsing error"""
    notify_payload: list[str] = ['{"a": "b"}']
    myqueue = _MockQueue()

    def my_iterator() -> _AsyncIterator:
        return _AsyncIterator(notify_payload)

    with patch(
        "extensions.eda.plugins.event_source.pg_listener.AsyncConnection.connect"
    ) as conn:
        mock_object = AsyncMock()
        conn.return_value = mock_object
        conn.return_value.__aenter__.side_effect = psycopg.OperationalError("Kaboom")
        mock_object.cursor = AsyncMock
        mock_object.notifies = my_iterator
        with pytest.raises(psycopg.OperationalError):
            asyncio.run(
                pg_listener_main(
                    myqueue,
                    {
                        "dsn": (
                            "host=localhost dbname=mydb "
                            "user=postgres password=password"
                        ),
                        "channels": ["test"],
                    },
                )
            )
