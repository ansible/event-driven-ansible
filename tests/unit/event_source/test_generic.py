"""Tests for generic source plugin"""

import asyncio
import os
import tempfile
from typing import Any

import pytest
import yaml

from extensions.eda.plugins.event_source.generic import (
    EnvVarMismatchError,
    MissingEnvVarError,
)
from extensions.eda.plugins.event_source.generic import main as generic_main


class _MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, item: Any) -> None:
        """Put an event into the queue"""
        self.queue.append(item)


TEST_PAYLOADS = [
    [{"a": 1, "b": 2}, {"name": "Fred", "kids": ["Pebbles"]}],
    [{"blob": "x" * 9000, "huge": "h" * 9000}],
    [{"a": 1, "x": 2}, {"x": "y" * 20000, "fail": False, "pi": 3.14159}],
]


@pytest.mark.parametrize("events", TEST_PAYLOADS)
def test_generic(events: Any) -> None:
    """Test receiving different payloads from generic."""
    myqueue = _MockQueue()

    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": events,
            },
        )
    )

    assert len(myqueue.queue) == len(events)
    index = 0
    for event in events:
        assert myqueue.queue[index] == event
        index += 1


def test_generic_loop_count() -> None:
    """Test receiving events multiple times."""
    myqueue = _MockQueue()
    event = {"name": "fred"}
    loop_count = 3

    asyncio.run(
        generic_main(
            myqueue,
            {"payload": [event], "loop_count": loop_count},
        )
    )

    assert len(myqueue.queue) == loop_count
    index = 0
    for _i in range(loop_count):
        assert myqueue.queue[index] == event
        index += 1


def test_generic_create_index() -> None:
    """Test receiving events with index."""
    myqueue = _MockQueue()
    event = {"name": "fred"}
    loop_count = 3

    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": [event],
                "loop_count": loop_count,
                "create_index": "sequence",
            },
        )
    )

    assert len(myqueue.queue) == loop_count
    index = 0
    for i in range(loop_count):
        expected_event = {"name": "fred", "sequence": i}
        assert myqueue.queue[index] == expected_event
        index += 1


def test_generic_final_payload() -> None:
    """Test receiving events with final payload."""
    myqueue = _MockQueue()
    event = {"name": "fred"}
    loop_count = 3
    final_payload = {"finito": True}

    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": [event],
                "loop_count": loop_count,
                "final_payload": final_payload,
            },
        )
    )

    assert len(myqueue.queue) == loop_count + 1
    index = 0
    for _i in range(loop_count):
        assert myqueue.queue[index] == event
        index += 1

    assert myqueue.queue[index] == final_payload


def test_generic_blob() -> None:
    """Test receiving events with final payload."""
    myqueue = _MockQueue()
    event = {"name": "fred"}
    blob_size = 95

    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": event,
                "blob_size": blob_size,
            },
        )
    )

    assert len(myqueue.queue) == 1
    assert myqueue.queue[0] == {"name": "fred", "blob": "x" * blob_size}


TEST_TIME_FORMATS = [["iso8601", str], ["local", str], ["epoch", int]]


@pytest.mark.parametrize("time_format,expected_type", TEST_TIME_FORMATS)
def test_generic_timestamps(time_format: list[str], expected_type: type) -> None:
    """Test receiving events with timestamps."""
    myqueue = _MockQueue()
    event = {"name": "fred"}

    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": event,
                "time_format": time_format,
                "timestamp": True,
            },
        )
    )

    assert len(myqueue.queue) == 1
    assert isinstance(myqueue.queue[0]["timestamp"], expected_type)


def test_generic_bad_time_format() -> None:
    """Test bad time format."""
    myqueue = _MockQueue()
    event = {"name": "fred"}

    with pytest.raises(ValueError):
        asyncio.run(
            generic_main(
                myqueue,
                {
                    "payload": event,
                    "time_format": "nada",
                    "timestamp": True,
                },
            )
        )


def test_generic_payload_file() -> None:
    """Test reading events from file."""
    myqueue = _MockQueue()
    event = {"name": "fred"}
    loop_count = 2

    with tempfile.NamedTemporaryFile() as tmpfile:
        with open(tmpfile.name, "w") as f:
            yaml.dump(event, f)
        asyncio.run(
            generic_main(
                myqueue,
                {
                    "payload_file": tmpfile.name,
                    "loop_count": loop_count,
                    "create_index": "sequence",
                },
            )
        )

    assert len(myqueue.queue) == loop_count
    index = 0
    for i in range(loop_count):
        expected_event = {"name": "fred", "sequence": i}
        assert myqueue.queue[index] == expected_event
        index += 1


def test_generic_missing_payload_file() -> None:
    """Test reading events from missing file."""
    myqueue = _MockQueue()
    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, "missing.yaml")
        with pytest.raises(ValueError):
            asyncio.run(
                generic_main(
                    myqueue,
                    {
                        "payload_file": fname,
                    },
                )
            )


def test_generic_parsing_payload_file() -> None:
    """Test parsing failure events from file."""
    myqueue = _MockQueue()
    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, "bogus.yaml")
        with open(fname, "w") as f:
            f.write("fail_text: 'Hello, I'm testing!'")

        with pytest.raises(ValueError):
            asyncio.run(
                generic_main(
                    myqueue,
                    {
                        "payload_file": fname,
                    },
                )
            )


def test_env_vars_missing() -> None:
    """Test missing env vars"""
    myqueue = _MockQueue()
    event = {"name": "fred"}

    with pytest.raises(MissingEnvVarError):
        asyncio.run(
            generic_main(
                myqueue,
                {
                    "payload": event,
                    "check_env_vars": {"NAME_MISSING": "Fred"},
                },
            )
        )


def test_env_vars_mismatch() -> None:
    """Test env vars with incorrect values"""
    myqueue = _MockQueue()
    event = {"name": "fred"}

    os.environ["TEST_ENV1"] = "Kaboom"
    with pytest.raises(EnvVarMismatchError):
        asyncio.run(
            generic_main(
                myqueue,
                {
                    "payload": event,
                    "check_env_vars": {"TEST_ENV1": "Fred"},
                },
            )
        )


def test_env_vars() -> None:
    """Test env vars with correct values"""
    myqueue = _MockQueue()
    event = {"name": "fred"}

    os.environ["TEST_ENV1"] = "Fred"
    asyncio.run(
        generic_main(
            myqueue,
            {
                "payload": event,
                "check_env_vars": {"TEST_ENV1": "Fred"},
            },
        )
    )
    assert len(myqueue.queue) == 1
    assert myqueue.queue[0] == {"name": "fred"}
