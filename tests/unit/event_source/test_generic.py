""" Tests for generic source plugin """

import asyncio

import pytest

from extensions.eda.plugins.event_source.generic import main as generic_main


class _MockQueue:
    def __init__(self):
        self.queue = []

    async def put(self, event):
        """Put an event into the queue"""
        self.queue.append(event)


TEST_PAYLOADS = [
    [{"a": 1, "b": 2}, {"name": "Fred", "kids": ["Pebbles"]}],
    [{"blob": "x" * 9000, "huge": "h" * 9000}],
    [{"a": 1, "x": 2}, {"x": "y" * 20000, "fail": False, "pi": 3.14159}],
]


@pytest.mark.parametrize("events", TEST_PAYLOADS)
def test_generic(events):
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


def test_generic_loop_count():
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


def test_generic_create_index():
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


def test_generic_final_payload():
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


def test_generic_blob():
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
def test_generic_timestamps(time_format, expected_type):
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


def test_generic_bad_time_format():
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
