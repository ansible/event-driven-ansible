from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from asyncmock import AsyncMock

from extensions.eda.plugins.event_source.kafka import get_message_timestamp
from extensions.eda.plugins.event_source.kafka import main as kafka_main

TEST_ITEMS_COUNT = 2


class MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, item: Any) -> None:
        self.queue.append(item)


class MockFeedbackQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.get_count = 0

    async def get(self) -> Any:
        self.get_count += 1
        return "ack"


@pytest.fixture
def myqueue() -> MockQueue:
    return MockQueue()


class AsyncIterator:
    def __init__(
        self,
        count: int = TEST_ITEMS_COUNT,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timestamp: int = 1708714664000,
        topic: str = "test-topic",
        partition: int = 0,
        offset: int = 0,
    ) -> None:
        self.max_count = count
        self.count = 0
        self.headers = headers or {"foo": "bar"}
        self.body = body
        self.timestamp = timestamp
        self.topic = topic
        self.partition = partition
        self.offset = offset

    async def __anext__(self) -> MagicMock:
        if self.count < self.max_count:
            mock = MagicMock()
            if self.body:
                mock.value = json.dumps(self.body).encode("utf-8")
            else:
                mock.value = f'{{"i": {self.count}}}'.encode("utf-8")
            mock.headers = [
                (key, value.encode("utf-8")) for key, value in self.headers.items()
            ]
            mock.timestamp = self.timestamp
            mock.topic = self.topic
            mock.partition = self.partition
            mock.offset = self.offset + self.count
            self.count += 1
            return mock
        else:
            raise StopAsyncIteration


class MockConsumer(AsyncMock):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.async_iterator: AsyncIterator | None = None
        self.commit_count = 0

    def __aiter__(self) -> AsyncIterator:
        if self.async_iterator is None:
            self.async_iterator = AsyncIterator()
        return self.async_iterator

    def subscribe(self, topics: list[str], pattern: str | None = None) -> None:
        assert topics or pattern
        assert not (topics and pattern)

    async def commit(self) -> None:
        self.commit_count += 1


@pytest.mark.parametrize(
    "topic_type, topic_value",
    [("topic", "eda"), ("topics", ["eda1", "eda2"]), ("topic_pattern", "eda_*")],
)
def test_receive_from_kafka_place_in_queue(
    myqueue: MockQueue,
    topic_type: str,
    topic_value: str | list[str],
) -> None:
    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumer,
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    topic_type: topic_value,
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                },
            ),
        )
        assert myqueue.queue[0]["body"] == {"i": 0}
        assert myqueue.queue[0]["meta"]["headers"] == {"foo": "bar"}
        # Check for the new meta fields: uuid and produced_at
        assert "uuid" in myqueue.queue[0]["meta"]
        assert "produced_at" in myqueue.queue[0]["meta"]
        assert myqueue.queue[0]["meta"]["uuid"] == "test-topic:0:0"
        assert len(myqueue.queue) == TEST_ITEMS_COUNT


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
    myqueue: MockQueue,
    topic_args: dict[str, Any],
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one of topic, topics, or topic_pattern must be provided.",
    ):
        asyncio.run(kafka_main(myqueue, topic_args))


def test_message_uuid_in_headers(myqueue: MockQueue) -> None:
    """Test that message_uuid from headers is used as the event uuid."""

    class MockConsumerWithUUID(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(
                count=1,
                headers={"message_uuid": "test-uuid-123", "foo": "bar"},
            )
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerWithUUID,
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
            ),
        )
        assert len(myqueue.queue) == 1
        assert myqueue.queue[0]["meta"]["uuid"] == "test-uuid-123"
        assert myqueue.queue[0]["meta"]["headers"]["message_uuid"] == "test-uuid-123"


def test_message_uuid_in_body(myqueue: MockQueue) -> None:
    """Test that message_uuid from body overrides the generated uuid."""

    class MockConsumerWithBodyUUID(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(
                count=1,
                headers={"foo": "bar"},
                body={"message_uuid": "body-uuid-456", "data": "test"},
            )
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerWithBodyUUID,
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
            ),
        )
        assert len(myqueue.queue) == 1
        assert myqueue.queue[0]["meta"]["uuid"] == "body-uuid-456"
        assert myqueue.queue[0]["body"]["message_uuid"] == "body-uuid-456"


def test_message_uuid_body_overrides_header(myqueue: MockQueue) -> None:
    """Test that message_uuid from body takes precedence over header."""

    class MockConsumerWithBothUUID(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(
                count=1,
                headers={"message_uuid": "header-uuid", "foo": "bar"},
                body={"message_uuid": "body-uuid", "data": "test"},
            )
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerWithBothUUID,
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
            ),
        )
        assert len(myqueue.queue) == 1
        # Body uuid should override header uuid
        assert myqueue.queue[0]["meta"]["uuid"] == "body-uuid"


def test_generated_uuid_from_coordinates(myqueue: MockQueue) -> None:
    """Test that uuid is generated from topic:partition:offset when not provided."""

    class MockConsumerWithCoordinates(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(
                count=1,
                headers={"foo": "bar"},
                body={"data": "test"},
                topic="my-topic",
                partition=5,
                offset=100,
            )
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerWithCoordinates,
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
            ),
        )
        assert len(myqueue.queue) == 1
        assert myqueue.queue[0]["meta"]["uuid"] == "my-topic:5:100"


def test_produced_at_timestamp(myqueue: MockQueue) -> None:
    """Test that produced_at timestamp is correctly formatted."""

    class MockConsumerWithTimestamp(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            # 1708714664000 ms = 2024-02-23T18:57:44.000Z
            self.async_iterator = AsyncIterator(
                count=1,
                headers={"foo": "bar"},
                body={"data": "test"},
                timestamp=1708714664000,
            )
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerWithTimestamp,
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
            ),
        )
        assert len(myqueue.queue) == 1
        assert "produced_at" in myqueue.queue[0]["meta"]
        # Verify the timestamp is in ISO format with Z suffix
        assert myqueue.queue[0]["meta"]["produced_at"] == "2024-02-23T18:57:44Z"


def test_feedback_queue_integration(myqueue: MockQueue) -> None:
    """Test that feedback queue is used when provided."""
    feedback_queue = MockFeedbackQueue()
    commit_count_tracker = {"count": 0}

    class MockConsumerForFeedback(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=TEST_ITEMS_COUNT)
            return self.async_iterator

        async def commit(self) -> None:
            commit_count_tracker["count"] += 1

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerForFeedback,
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "eda_feedback_queue": feedback_queue,
                },
            ),
        )
        # Verify that feedback queue was called for each message
        assert feedback_queue.get_count == TEST_ITEMS_COUNT
        # Verify that commit was called for each message
        assert commit_count_tracker["count"] == TEST_ITEMS_COUNT
        # Verify messages were processed
        assert len(myqueue.queue) == TEST_ITEMS_COUNT


def test_feedback_queue_disables_auto_commit() -> None:
    """Test that enable_auto_commit is False when feedback queue is provided."""
    myqueue = MockQueue()
    feedback_queue = MockFeedbackQueue()
    auto_commit_value = {"value": None}

    class MockConsumerCheckAutoCommit(MockConsumer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            # Capture the enable_auto_commit value only if present in kwargs
            # (AsyncMock creates child mocks that also call __init__)
            if "enable_auto_commit" in kwargs:
                auto_commit_value["value"] = kwargs["enable_auto_commit"]

        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1)
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerCheckAutoCommit,
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "eda_feedback_queue": feedback_queue,
                },
            ),
        )
        # Verify that enable_auto_commit was set to False
        assert auto_commit_value["value"] is False


def test_no_feedback_queue_enables_auto_commit() -> None:
    """Test that enable_auto_commit is True when feedback queue is not provided."""
    myqueue = MockQueue()
    auto_commit_value = {"value": None}

    class MockConsumerCheckAutoCommitTrue(MockConsumer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            # Capture the enable_auto_commit value only if present in kwargs
            # (AsyncMock creates child mocks that also call __init__)
            if "enable_auto_commit" in kwargs:
                auto_commit_value["value"] = kwargs["enable_auto_commit"]

        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1)
            return self.async_iterator

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumerCheckAutoCommitTrue,
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
            ),
        )
        # Verify that enable_auto_commit was set to True
        assert auto_commit_value["value"] is True


def test_get_message_timestamp() -> None:
    """Test the get_message_timestamp utility function."""
    from aiokafka.structs import ConsumerRecord

    # Create a mock ConsumerRecord with a timestamp
    # 1708714664000 ms = 2024-02-23T18:57:44.000Z
    mock_record = MagicMock(spec=ConsumerRecord)
    mock_record.timestamp = 1708714664000

    result = get_message_timestamp(mock_record)
    assert result == "2024-02-23T18:57:44Z"

    # Test with a different timestamp
    # 1609459200000 ms = 2021-01-01T00:00:00.000Z
    mock_record.timestamp = 1609459200000
    result = get_message_timestamp(mock_record)
    assert result == "2021-01-01T00:00:00Z"


def test_unicode_error_decoding_headers(myqueue: MockQueue) -> None:
    """Test that UnicodeError when decoding headers is handled gracefully."""

    class MockConsumerWithBadHeaders(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1)
            return self.async_iterator

    # Create a mock message with headers that will raise UnicodeError
    async def mock_anext_bad_headers(self: AsyncIterator) -> MagicMock:
        if self.count < self.max_count:
            mock = MagicMock()
            mock.value = b'{"data": "test"}'
            # Create a header that will raise UnicodeError when decoded
            bad_header = MagicMock()
            bad_header.__getitem__ = lambda s, i: b"key" if i == 0 else b"\xff\xfe"
            bad_header.decode = MagicMock(
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "")
            )
            mock.headers = [bad_header]
            mock.timestamp = 1708714664000
            mock.topic = "test-topic"
            mock.partition = 0
            mock.offset = 0
            self.count += 1
            return mock
        raise StopAsyncIteration

    with patch.object(AsyncIterator, "__anext__", mock_anext_bad_headers):
        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=MockConsumerWithBadHeaders,
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
                ),
            )
            # Message should still be processed despite header decoding error
            assert len(myqueue.queue) == 1
            assert myqueue.queue[0]["body"]["data"] == "test"


def test_json_decode_error(myqueue: MockQueue) -> None:
    """Test that JSONDecodeError is handled and raw value is stored."""

    class MockConsumerWithInvalidJSON(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1, headers={"foo": "bar"})
            return self.async_iterator

    # Create a mock message with invalid JSON
    async def mock_anext_bad_json(self: AsyncIterator) -> MagicMock:
        if self.count < self.max_count:
            mock = MagicMock()
            # Invalid JSON - not properly formatted
            mock.value = b"not valid json {{{{"
            mock.headers = [(b"foo", b"bar")]
            mock.timestamp = 1708714664000
            mock.topic = "test-topic"
            mock.partition = 0
            mock.offset = 0
            self.count += 1
            return mock
        raise StopAsyncIteration

    with patch.object(AsyncIterator, "__anext__", mock_anext_bad_json):
        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=MockConsumerWithInvalidJSON,
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
                ),
            )
            # Raw value should be stored when JSON decode fails
            assert len(myqueue.queue) == 1
            assert myqueue.queue[0]["body"] == "not valid json {{{{"


def test_unicode_error_decoding_body(myqueue: MockQueue) -> None:
    """Test that UnicodeError when decoding message body is handled."""

    class MockConsumerWithBadBody(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1)
            return self.async_iterator

    # Create a mock message with body that will raise UnicodeError
    async def mock_anext_bad_body(self: AsyncIterator) -> MagicMock:
        if self.count < self.max_count:
            mock = MagicMock()
            # Create a value that will raise UnicodeError when decoded
            mock.value = MagicMock()
            mock.value.decode = MagicMock(
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, ""),
            )
            mock.headers = [(b"foo", b"bar")]
            mock.timestamp = 1708714664000
            mock.topic = "test-topic"
            mock.partition = 0
            mock.offset = 0
            self.count += 1
            return mock
        raise StopAsyncIteration

    with patch.object(AsyncIterator, "__anext__", mock_anext_bad_body):
        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=MockConsumerWithBadBody,
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
                ),
            )
            # No message should be added to queue when body decoding fails
            # because data is set to None and the "if data:" check prevents queueing
            assert len(myqueue.queue) == 0


def test_empty_data_not_queued(myqueue: MockQueue) -> None:
    """Test that messages with empty/None data are not queued."""

    class MockConsumerWithEmptyData(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=1)
            return self.async_iterator

    # Create a mock message that results in empty data
    async def mock_anext_empty_data(self: AsyncIterator) -> MagicMock:
        if self.count < self.max_count:
            mock = MagicMock()
            # Empty JSON object/string
            mock.value = b'""'
            mock.headers = [(b"foo", b"bar")]
            mock.timestamp = 1708714664000
            mock.topic = "test-topic"
            mock.partition = 0
            mock.offset = 0
            self.count += 1
            return mock
        raise StopAsyncIteration

    with patch.object(AsyncIterator, "__anext__", mock_anext_empty_data):
        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=MockConsumerWithEmptyData,
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
                ),
            )
            # Empty string data should not be queued (falsy value)
            assert len(myqueue.queue) == 0


def test_feedback_enabled_without_queue_raises_error(myqueue: MockQueue) -> None:
    """Test that feedback=true without a queue raises ValueError."""
    with pytest.raises(
        ValueError,
        match="feedback: true was set but no feedback queue was provided",
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "feedback": True,
                    # No eda_feedback_queue provided
                },
            ),
        )


def test_feedback_disabled_without_queue_succeeds(myqueue: MockQueue) -> None:
    """Test that feedback=false without a queue works fine."""
    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumer,
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "feedback": False,
                    # No eda_feedback_queue provided, but that's ok since feedback=false
                },
            ),
        )
        # Should process messages normally
        assert len(myqueue.queue) == TEST_ITEMS_COUNT


def test_feedback_enabled_with_queue_succeeds(myqueue: MockQueue) -> None:
    """Test that feedback=true with a queue works correctly."""
    feedback_queue = MockFeedbackQueue()

    with patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
        new=MockConsumer,
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "feedback": True,
                    "eda_feedback_queue": feedback_queue,
                },
            ),
        )
        # Should process messages normally
        assert len(myqueue.queue) == TEST_ITEMS_COUNT
        # Feedback queue should have been called
        assert feedback_queue.get_count == TEST_ITEMS_COUNT


def test_feedback_queue_timeout(myqueue: MockQueue) -> None:
    """Test that TimeoutError when waiting for feedback is handled gracefully."""

    class MockFeedbackQueueTimeout(asyncio.Queue[Any]):
        async def get(self) -> Any:
            # Simulate a long wait that will timeout
            # wait_for will raise TimeoutError when this takes too long
            await asyncio.sleep(200)  # Sleep longer than QUEUE_TIMEOUT (120s)
            return "ack"

    feedback_queue = MockFeedbackQueueTimeout()
    commit_count_tracker = {"count": 0}

    class MockConsumerForTimeout(MockConsumer):
        def __aiter__(self) -> AsyncIterator:
            self.async_iterator = AsyncIterator(count=TEST_ITEMS_COUNT)
            return self.async_iterator

        async def commit(self) -> None:
            # This should not be called when timeout occurs
            commit_count_tracker["count"] += 1

    # Mock asyncio.wait_for to immediately raise TimeoutError
    async def mock_wait_for(coroutine: Any, timeout: float) -> Any:
        # Cancel the coroutine and raise TimeoutError immediately
        if hasattr(coroutine, "close"):
            coroutine.close()
        raise asyncio.TimeoutError

    with (
        patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=MockConsumerForTimeout,
        ),
        patch("asyncio.wait_for", side_effect=mock_wait_for),
    ):
        asyncio.run(
            kafka_main(
                myqueue,
                {
                    "topic": "eda",
                    "host": "localhost",
                    "port": "9092",
                    "group_id": "test",
                    "eda_feedback_queue": feedback_queue,
                },
            ),
        )
        # Messages should still be queued despite timeout
        assert len(myqueue.queue) == TEST_ITEMS_COUNT
        # Commit should not be called when timeout occurs
        assert commit_count_tracker["count"] == 0
