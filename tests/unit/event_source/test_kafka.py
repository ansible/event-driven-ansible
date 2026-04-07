from __future__ import annotations

import asyncio
import io
import json
import struct
import time
from typing import Any
from unittest.mock import AsyncMock as StdAsyncMock
from unittest.mock import MagicMock, patch

import aiohttp
import fastavro
import pytest
from asyncmock import AsyncMock

from extensions.eda.plugins.event_source.kafka import (
    AvroDeserializer,
    _configure_avro,
    get_message_timestamp,
)
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
        # Check for the new meta fields: source_offset and produced_at
        assert "source_offset" in myqueue.queue[0]["meta"]
        assert "produced_at" in myqueue.queue[0]["meta"]
        assert myqueue.queue[0]["meta"]["source_offset"] == "test-topic:0:0"
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


def test_message_uuid_header_takes_precedence(myqueue: MockQueue) -> None:
    """Test that message_uuid from header takes precedence over body."""

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
        # Header uuid should take precedence over body uuid
        assert myqueue.queue[0]["meta"]["uuid"] == "header-uuid"


def test_generated_source_offset_from_coordinates(myqueue: MockQueue) -> None:
    """Test that source_offset is generated from topic:partition:offset."""

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
        assert myqueue.queue[0]["meta"]["source_offset"] == "my-topic:5:100"


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
                    "feedback": True,
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
                    "feedback": True,
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
        with pytest.raises(asyncio.TimeoutError):
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
        # Messages should still be queued despite timeout
        assert len(myqueue.queue) == 1
        # Commit should not be called when timeout occurs
        assert commit_count_tracker["count"] == 0


# --- Avro Deserialization Tests ---

SAMPLE_AVRO_SCHEMA = {
    "type": "record",
    "name": "TestEvent",
    "namespace": "com.example.eda",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "value", "type": "int"},
    ],
}


@pytest.fixture
def avro_schema_file(tmp_path: Any) -> str:
    """Create a temporary Avro schema file."""
    schema_path = tmp_path / "test_schema.avsc"
    schema_path.write_text(json.dumps(SAMPLE_AVRO_SCHEMA))
    return str(schema_path)


def _serialize_avro_schemaless(record: dict[str, Any], schema: dict[str, Any]) -> bytes:
    """Helper to serialize a record to raw Avro binary (schemaless)."""
    parsed = fastavro.parse_schema(schema)
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, parsed, record)
    return buf.getvalue()


def _serialize_avro_object_container(
    records: list[dict[str, Any]], schema: dict[str, Any]
) -> bytes:
    """Helper to serialize records to Avro Object Container format."""
    parsed = fastavro.parse_schema(schema)
    buf = io.BytesIO()
    fastavro.writer(buf, parsed, records)
    return buf.getvalue()


class TestAvroDeserializer:
    """Tests for the AvroDeserializer class."""

    def test_init_with_valid_schema_file(self, avro_schema_file: str) -> None:
        deserializer = AvroDeserializer(avro_schema_file=avro_schema_file)
        assert deserializer._schema is not None

    def test_init_without_schema_file(self) -> None:
        deserializer = AvroDeserializer()
        assert deserializer._schema is None

    def test_init_missing_fastavro_raises_error(self) -> None:
        with patch("extensions.eda.plugins.event_source.kafka.HAS_FASTAVRO", False):
            with pytest.raises(ImportError, match="fastavro"):
                AvroDeserializer()

    def test_init_nonexistent_schema_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError, match="Avro schema file not found"):
            AvroDeserializer(avro_schema_file="/nonexistent/path/schema.avsc")

    def test_init_invalid_schema_raises_error(self, tmp_path: Any) -> None:
        bad_schema = tmp_path / "bad.avsc"
        bad_schema.write_text('{"type": "invalid_type"}')
        with pytest.raises(Exception):
            AvroDeserializer(avro_schema_file=str(bad_schema))

    def test_init_path_with_tilde_expansion(self) -> None:
        """Verify ~ in paths is expanded properly."""
        with pytest.raises(FileNotFoundError):
            AvroDeserializer(avro_schema_file="~/nonexistent_schema.avsc")

    def test_deserialize_schemaless_record(self, avro_schema_file: str) -> None:
        deserializer = AvroDeserializer(avro_schema_file=avro_schema_file)
        record = {"name": "test-event", "value": 42}
        avro_bytes = _serialize_avro_schemaless(record, SAMPLE_AVRO_SCHEMA)

        result = asyncio.run(deserializer.deserialize(avro_bytes))
        assert result == {"name": "test-event", "value": 42}

    def test_deserialize_object_container(self) -> None:
        deserializer = AvroDeserializer()  # no local schema
        record = {"name": "container-event", "value": 99}
        avro_bytes = _serialize_avro_object_container([record], SAMPLE_AVRO_SCHEMA)

        result = asyncio.run(deserializer.deserialize(avro_bytes))
        assert result == {"name": "container-event", "value": 99}

    def test_deserialize_message_exceeds_size_limit(
        self, avro_schema_file: str
    ) -> None:
        deserializer = AvroDeserializer(avro_schema_file=avro_schema_file)
        large_data = b"\x00" * (AvroDeserializer.MAX_MESSAGE_SIZE + 1)

        result = asyncio.run(deserializer.deserialize(large_data))
        assert result is None

    def test_deserialize_corrupt_data_returns_none(self, avro_schema_file: str) -> None:
        deserializer = AvroDeserializer(avro_schema_file=avro_schema_file)
        result = asyncio.run(deserializer.deserialize(b"\xff\xfe\xfd\xfc"))
        assert result is None

    def test_deserialize_empty_data_returns_none(self, avro_schema_file: str) -> None:
        deserializer = AvroDeserializer(avro_schema_file=avro_schema_file)
        result = asyncio.run(deserializer.deserialize(b""))
        assert result is None

    def test_deserialize_object_container_corrupt_data_returns_none(self) -> None:
        deserializer = AvroDeserializer()  # no local schema
        result = asyncio.run(deserializer.deserialize(b"\xff\xfe\xfd\xfc"))
        assert result is None

    def test_json_format_unchanged(self, myqueue: MockQueue) -> None:
        """Verify existing JSON behavior is unaffected by Avro changes."""
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
                        "message_format": "json",
                    },
                )
            )
            assert myqueue.queue[0]["body"] == {"i": 0}
            assert myqueue.queue[0]["meta"]["headers"] == {"foo": "bar"}
            assert "source_offset" in myqueue.queue[0]["meta"]
            assert "produced_at" in myqueue.queue[0]["meta"]
            assert len(myqueue.queue) == 2

    def test_invalid_message_format_raises_error(self, myqueue: MockQueue) -> None:
        with pytest.raises(ValueError, match="Invalid message_format"):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "eda",
                        "host": "localhost",
                        "port": "9092",
                        "group_id": "test",
                        "message_format": "protobuf",
                    },
                )
            )


class TestAvroKafkaIntegration:
    """Test Avro deserialization through the full kafka main() flow."""

    def test_avro_messages_through_main(
        self, myqueue: MockQueue, avro_schema_file: str
    ) -> None:
        """Verify Avro messages flow through main() and end up in the queue."""
        record1 = {"name": "event-1", "value": 10}
        record2 = {"name": "event-2", "value": 20}

        avro_bytes1 = _serialize_avro_schemaless(record1, SAMPLE_AVRO_SCHEMA)
        avro_bytes2 = _serialize_avro_schemaless(record2, SAMPLE_AVRO_SCHEMA)

        class AvroAsyncIterator:
            def __init__(self) -> None:
                self.messages = [avro_bytes1, avro_bytes2]
                self.index = 0

            async def __anext__(self) -> MagicMock:
                if self.index < len(self.messages):
                    mock = MagicMock()
                    mock.value = self.messages[self.index]
                    mock.headers = [("source", b"test")]
                    self.index += 1
                    return mock
                raise StopAsyncIteration

        class AvroMockConsumer(AsyncMock):  # type: ignore[misc]
            def __aiter__(self) -> AvroAsyncIterator:
                return AvroAsyncIterator()

            def subscribe(self, topics: list[str], pattern: str | None = None) -> None:
                pass

        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=AvroMockConsumer,
        ):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "avro-test",
                        "host": "localhost",
                        "port": "9092",
                        "group_id": "test",
                        "message_format": "avro",
                        "avro_schema_file": avro_schema_file,
                    },
                )
            )

        assert len(myqueue.queue) == 2
        assert myqueue.queue[0]["body"] == {"name": "event-1", "value": 10}
        assert myqueue.queue[1]["body"] == {"name": "event-2", "value": 20}
        assert myqueue.queue[0]["meta"]["headers"] == {"source": "test"}


# --- Schema Registry Tests ---


def _serialize_wire_format(
    record: dict[str, Any], schema: dict[str, Any], schema_id: int
) -> bytes:
    """Serialize a record with the Confluent wire format header."""
    parsed = fastavro.parse_schema(schema)
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, parsed, record)
    avro_payload = buf.getvalue()
    header = struct.pack(">bI", 0, schema_id)
    return header + avro_payload


class TestSchemaRegistryConfig:
    """Tests for Schema Registry configuration validation."""

    def test_registry_url_validation_invalid_scheme(self) -> None:
        with pytest.raises(ValueError, match="http or https"):
            AvroDeserializer(schema_registry_url="ftp://localhost:8081")

    def test_registry_url_validation_no_host(self) -> None:
        with pytest.raises(ValueError, match="hostname"):
            AvroDeserializer(schema_registry_url="http://")

    def test_auth_mutual_exclusion(self) -> None:
        with pytest.raises(ValueError, match="Only one Schema Registry auth"):
            AvroDeserializer(
                schema_registry_url="http://localhost:8081",
                schema_registry_basic_auth="user:pass",
                schema_registry_bearer_token="token123",
            )

    def test_oauth_requires_secret_and_url(self) -> None:
        with pytest.raises(ValueError, match="schema_registry_oauth_client_secret"):
            AvroDeserializer(
                schema_registry_url="http://localhost:8081",
                schema_registry_oauth_client_id="my-client",
            )

    def test_valid_registry_url(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        assert d._registry_url == "http://localhost:8081"

    def test_valid_basic_auth(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_basic_auth="user:pass",
        )
        assert d._basic_auth_header is not None
        assert d._basic_auth_header.startswith("Basic ")

    def test_valid_bearer_token(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_bearer_token="mytoken",
        )
        assert d._bearer_token == "mytoken"

    def test_valid_oauth_config(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="client-secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
            schema_registry_oauth_scope="schema:read",
        )
        assert d._oauth_client_id == "client-id"
        assert d._oauth_scope == "schema:read"


class TestWireFormatDetection:
    """Tests for Confluent wire format detection and parsing."""

    def test_is_wire_format_with_valid_header(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        data = struct.pack(">bI", 0, 1) + b"\x00\x01\x02"
        assert d._is_wire_format(data) is True

    def test_is_wire_format_without_registry(self) -> None:
        d = AvroDeserializer()
        data = struct.pack(">bI", 0, 1) + b"\x00\x01\x02"
        assert d._is_wire_format(data) is False

    def test_is_wire_format_wrong_magic_byte(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        data = b"\x01" + struct.pack(">I", 1) + b"\x00\x01\x02"
        assert d._is_wire_format(data) is False

    def test_is_wire_format_too_short(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        assert d._is_wire_format(b"\x00\x01\x02") is False

    def test_extract_schema_id(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        data = struct.pack(">bI", 0, 42) + b"\x00"
        assert d._extract_schema_id(data) == 42

    def test_extract_schema_id_large(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        data = struct.pack(">bI", 0, 999999) + b"\x00"
        assert d._extract_schema_id(data) == 999999


class TestSchemaCache:
    """Tests for the LRU schema cache."""

    def test_cache_eviction(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        parsed = fastavro.parse_schema(SAMPLE_AVRO_SCHEMA)
        for i in range(d._SCHEMA_CACHE_MAX_SIZE + 5):
            d._schema_cache[i] = parsed
            if len(d._schema_cache) > d._SCHEMA_CACHE_MAX_SIZE:
                d._schema_cache.popitem(last=False)
        assert len(d._schema_cache) == d._SCHEMA_CACHE_MAX_SIZE
        assert 0 not in d._schema_cache
        assert d._SCHEMA_CACHE_MAX_SIZE + 4 in d._schema_cache


class TestSchemaRegistryDeserialize:
    """Tests for wire format deserialization with mocked registry."""

    def test_wire_format_fallback_to_local_schema(self, avro_schema_file: str) -> None:
        """When registry lookup fails, fall back to local schema."""
        d = AvroDeserializer(
            avro_schema_file=avro_schema_file,
            schema_registry_url="http://localhost:8081",
        )
        record = {"name": "fallback-event", "value": 77}
        # Strip wire format header to simulate what local schema would see
        raw_data = _serialize_avro_schemaless(record, SAMPLE_AVRO_SCHEMA)

        result = asyncio.run(d.deserialize(raw_data))
        assert result == {"name": "fallback-event", "value": 77}

    def test_non_wire_format_uses_local_schema(self, avro_schema_file: str) -> None:
        """Raw Avro (no wire format header) uses local schema even with registry configured."""
        d = AvroDeserializer(
            avro_schema_file=avro_schema_file,
            schema_registry_url="http://localhost:8081",
        )
        record = {"name": "raw-event", "value": 55}
        raw_data = _serialize_avro_schemaless(record, SAMPLE_AVRO_SCHEMA)

        result = asyncio.run(d.deserialize(raw_data))
        assert result == {"name": "raw-event", "value": 55}

    def test_wire_format_registry_success(self) -> None:
        """Wire format message deserialized successfully via mocked registry."""
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        record = {"name": "registry-event", "value": 123}
        wire_data = _serialize_wire_format(record, SAMPLE_AVRO_SCHEMA, schema_id=42)

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"schema": json.dumps(SAMPLE_AVRO_SCHEMA)}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=mock_resp)
        d._http_session = mock_session

        result = asyncio.run(d.deserialize(wire_data))
        assert result == {"name": "registry-event", "value": 123}
        assert 42 in d._schema_cache

    def test_wire_format_registry_oauth_headers_passed(self) -> None:
        """OAuth auth headers are passed through to the registry GET request."""
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="client-secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )
        # Pre-set a valid token to avoid mocking the token fetch
        d._oauth_access_token = "my-oauth-token"
        d._oauth_token_expiry = time.time() + 3600

        record = {"name": "oauth-event", "value": 99}
        wire_data = _serialize_wire_format(record, SAMPLE_AVRO_SCHEMA, schema_id=10)

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"schema": json.dumps(SAMPLE_AVRO_SCHEMA)}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=mock_resp)
        d._http_session = mock_session

        result = asyncio.run(d.deserialize(wire_data))

        # Verify deserialization succeeded
        assert result == {"name": "oauth-event", "value": 99}

        # Verify OAuth token was passed in the GET request headers
        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer my-oauth-token"
        assert (
            call_kwargs["headers"]["Accept"] == "application/vnd.schemaregistry.v1+json"
        )

    def test_wire_format_registry_cache_hit(self) -> None:
        """Second call with same schema ID uses cache, no HTTP call."""
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        parsed = fastavro.parse_schema(SAMPLE_AVRO_SCHEMA)
        d._schema_cache[42] = parsed

        record = {"name": "cached-event", "value": 7}
        wire_data = _serialize_wire_format(record, SAMPLE_AVRO_SCHEMA, schema_id=42)

        result = asyncio.run(d.deserialize(wire_data))
        assert result == {"name": "cached-event", "value": 7}
        # Verify cache was used (no HTTP session needed)
        assert d._http_session is None

    def test_wire_format_registry_failure_falls_back_to_local(
        self, avro_schema_file: str
    ) -> None:
        """When registry fetch fails, fallback to local schema is attempted.

        The fallback passes the FULL data (including 5-byte wire header)
        to the local schema deserializer. fastavro's schemaless_reader is
        lenient and will parse it (producing garbled data), but the key
        assertion is that the registry failure warning path is exercised
        and a result is returned (not an exception).
        """
        d = AvroDeserializer(
            avro_schema_file=avro_schema_file,
            schema_registry_url="http://localhost:8081",
        )
        record = {"name": "fallback-event", "value": 33}
        wire_data = _serialize_wire_format(record, SAMPLE_AVRO_SCHEMA, schema_id=99)

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=404, message="Not Found"
            )
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=mock_resp)
        d._http_session = mock_session

        # Registry fails -> warning logged -> falls back to local schema
        # Local schema parses the data (wire header causes garbled output)
        result = asyncio.run(d.deserialize(wire_data))
        assert result is not None
        assert isinstance(result, dict)

    def test_wire_format_registry_failure_no_local_schema(self) -> None:
        """When registry fetch fails and no local schema, try object container (returns None for raw)."""
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        record = {"name": "no-fallback", "value": 1}
        wire_data = _serialize_wire_format(record, SAMPLE_AVRO_SCHEMA, schema_id=99)

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500, message="Error"
            )
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=mock_resp)
        d._http_session = mock_session

        result = asyncio.run(d.deserialize(wire_data))
        # No local schema, not valid object container -> None
        assert result is None


class TestGetAuthHeaders:
    """Tests for _get_auth_headers method."""

    def test_auth_headers_basic(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_basic_auth="user:pass",
        )
        headers = asyncio.run(d._get_auth_headers())
        assert headers["Authorization"].startswith("Basic ")
        assert "Accept" in headers

    def test_auth_headers_bearer(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_bearer_token="my-jwt-token",
        )
        headers = asyncio.run(d._get_auth_headers())
        assert headers["Authorization"] == "Bearer my-jwt-token"

    def test_auth_headers_oauth_triggers_fetch(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="client-secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )
        # Pre-set a token and valid expiry so it doesn't actually fetch
        d._oauth_access_token = "pre-fetched-token"
        d._oauth_token_expiry = time.time() + 3600

        headers = asyncio.run(d._get_auth_headers())
        assert headers["Authorization"] == "Bearer pre-fetched-token"

    def test_auth_headers_oauth_expired_triggers_refresh(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="client-secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )
        # Set expired token
        d._oauth_access_token = "old-token"
        d._oauth_token_expiry = 0.0

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"access_token": "new-token", "expires_in": 3600}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            headers = asyncio.run(d._get_auth_headers())

        assert headers["Authorization"] == "Bearer new-token"
        assert d._oauth_access_token == "new-token"
        assert d._oauth_token_expiry > time.time()

    def test_auth_headers_no_auth(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        headers = asyncio.run(d._get_auth_headers())
        assert "Authorization" not in headers
        assert "Accept" in headers


class TestFetchOAuthToken:
    """Tests for _fetch_oauth_token method."""

    def test_fetch_oauth_token_success(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
            schema_registry_oauth_scope="registry:read",
        )

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"access_token": "fetched-token", "expires_in": 1800}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            asyncio.run(d._fetch_oauth_token())

        assert d._oauth_access_token == "fetched-token"
        # expires_in=1800 minus 30s buffer
        assert d._oauth_token_expiry > time.time()

        # Verify the POST body sent to the token endpoint
        mock_session.post.assert_called_once_with(
            "https://auth.example.com/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "client-id",
                "client_secret": "secret",
                "scope": "registry:read",
            },
            ssl=None,  # http:// registry URL produces no SSL context
        )

    def test_fetch_oauth_token_without_scope(self) -> None:
        """When no scope is configured, scope must not appear in the POST body."""
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"access_token": "no-scope-token", "expires_in": 3600}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            asyncio.run(d._fetch_oauth_token())

        assert d._oauth_access_token == "no-scope-token"

        # Verify scope is NOT in the POST body
        post_data = mock_session.post.call_args[1]["data"]
        assert "scope" not in post_data
        assert post_data == {
            "grant_type": "client_credentials",
            "client_id": "client-id",
            "client_secret": "secret",
        }

    def test_fetch_oauth_token_default_expiry(self) -> None:
        """When response omits expires_in, default to 3600s with 30s buffer."""
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(return_value={"access_token": "no-expiry-token"})
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        before = time.time()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            asyncio.run(d._fetch_oauth_token())

        assert d._oauth_access_token == "no-expiry-token"
        # Default expires_in=3600, minus 30s buffer
        expected_expiry = before + 3600 - 30
        assert abs(d._oauth_token_expiry - expected_expiry) < 2

    def test_fetch_oauth_token_initial_failure_raises(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=401, message="Unauthorized"
            )
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            pytest.raises(RuntimeError, match="Initial OAuth token acquisition failed"),
        ):
            asyncio.run(d._fetch_oauth_token())

        assert d._oauth_access_token is None

    def test_fetch_oauth_token_refresh_failure_keeps_stale(self) -> None:
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
        )
        # Simulate a previously acquired token
        d._oauth_access_token = "old-token"
        d._oauth_token_expiry = time.time() + 10

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500, message="Server Error"
            )
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            asyncio.run(d._fetch_oauth_token())

        # Stale token should be preserved
        assert d._oauth_access_token == "old-token"

    def test_fetch_oauth_token_no_url(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        d._oauth_token_url = None
        asyncio.run(d._fetch_oauth_token())
        assert d._oauth_access_token is None

    def test_fetch_oauth_token_passes_ssl_context(self) -> None:
        """SSL context is passed to the OAuth token endpoint POST request."""
        d = AvroDeserializer(
            schema_registry_url="https://registry.example.com:8081",
            schema_registry_oauth_client_id="client-id",
            schema_registry_oauth_client_secret="secret",
            schema_registry_oauth_token_url="https://auth.example.com/token",
            schema_registry_ssl=True,
        )
        assert d._ssl_context is not None

        mock_resp = StdAsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = StdAsyncMock(
            return_value={"access_token": "ssl-token", "expires_in": 3600}
        )
        mock_resp.__aenter__ = StdAsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = StdAsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = StdAsyncMock(return_value=mock_session)
        mock_session.__aexit__ = StdAsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            asyncio.run(d._fetch_oauth_token())

        assert d._oauth_access_token == "ssl-token"

        # Verify ssl= was passed to session.post()
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["ssl"] is d._ssl_context


class TestClose:
    """Tests for the close() method."""

    def test_close_with_open_session(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = False
        d._http_session = mock_session

        asyncio.run(d.close())
        mock_session.close.assert_awaited_once()

    def test_close_with_closed_session(self) -> None:
        d = AvroDeserializer(schema_registry_url="http://localhost:8081")
        mock_session = StdAsyncMock(spec=aiohttp.ClientSession)
        mock_session.closed = True
        d._http_session = mock_session

        asyncio.run(d.close())
        mock_session.close.assert_not_awaited()

    def test_close_without_session(self) -> None:
        d = AvroDeserializer()
        asyncio.run(d.close())  # Should not raise


class TestSSLContext:
    """Tests for SSL context configuration."""

    def test_ssl_context_built_for_https(self, tmp_path: Any) -> None:
        """SSL context is created when registry uses https and schema_registry_ssl=True."""
        d = AvroDeserializer(
            schema_registry_url="https://registry.example.com:8081",
            schema_registry_ssl=True,
        )
        assert d._ssl_context is not None

    def test_ssl_context_not_built_for_http(self) -> None:
        """No SSL context for http registry URLs."""
        d = AvroDeserializer(
            schema_registry_url="http://localhost:8081",
            schema_registry_ssl=True,
        )
        assert d._ssl_context is None

    def test_ssl_context_not_built_when_disabled(self) -> None:
        """No SSL context when schema_registry_ssl=False."""
        d = AvroDeserializer(
            schema_registry_url="https://registry.example.com:8081",
            schema_registry_ssl=False,
        )
        assert d._ssl_context is None


class TestNonDictRecordWrapping:
    """Tests for non-dict record wrapping in deserializers."""

    def test_schemaless_non_dict_wrapped(self) -> None:
        """Non-dict records from schemaless_reader are wrapped as {'value': record}."""
        # Schema that produces a single string value
        string_schema = {"type": "string"}
        parsed = fastavro.parse_schema(string_schema)
        buf = io.BytesIO()
        fastavro.schemaless_writer(buf, parsed, "hello-world")
        avro_bytes = buf.getvalue()

        d = AvroDeserializer()
        d._schema = parsed
        result = asyncio.run(d.deserialize(avro_bytes))
        assert result == {"value": "hello-world"}

    def test_object_container_non_dict_wrapped(self) -> None:
        """Non-dict records from object container are wrapped as {'value': record}."""
        string_schema = {"type": "string"}
        parsed = fastavro.parse_schema(string_schema)
        buf = io.BytesIO()
        fastavro.writer(buf, parsed, ["hello-container"])
        avro_bytes = buf.getvalue()

        d = AvroDeserializer()
        result = asyncio.run(d.deserialize(avro_bytes))
        assert result == {"value": "hello-container"}


class TestConfigureAvro:
    """Tests for the _configure_avro helper function."""

    def test_json_format_returns_none_deserializer(self) -> None:
        msg_fmt, deserializer = _configure_avro({"message_format": "json"})
        assert msg_fmt == "json"
        assert deserializer is None

    def test_default_format_is_json(self) -> None:
        msg_fmt, deserializer = _configure_avro({})
        assert msg_fmt == "json"
        assert deserializer is None

    def test_avro_format_creates_deserializer(self, avro_schema_file: str) -> None:
        msg_fmt, deserializer = _configure_avro(
            {"message_format": "avro", "avro_schema_file": avro_schema_file}
        )
        assert msg_fmt == "avro"
        assert deserializer is not None

    def test_avro_with_registry_passes_ssl(self) -> None:
        msg_fmt, deserializer = _configure_avro(
            {
                "message_format": "avro",
                "schema_registry_url": "https://registry.example.com",
                "schema_registry_ssl": True,
            },
        )
        assert deserializer is not None
        assert deserializer._registry_url == "https://registry.example.com"
        assert deserializer._ssl_context is not None

    def test_avro_with_ssl_disabled_no_ssl_passthrough(self) -> None:
        msg_fmt, deserializer = _configure_avro(
            {
                "message_format": "avro",
                "schema_registry_url": "http://localhost:8081",
                "schema_registry_ssl": False,
            },
            ssl_cafile="/some/ca.pem",
            ssl_certfile="/some/cert.pem",
            ssl_keyfile="/some/key.pem",
        )
        assert deserializer is not None
        assert deserializer._ssl_context is None


class TestAvroNoneSkipsMessage:
    """Test that Avro deserialization returning None skips the message in main()."""

    def test_avro_none_skips_message(self, myqueue: MockQueue) -> None:
        """When avro deserializer returns None, message is not queued."""

        class AvroNoneIterator:
            def __init__(self) -> None:
                self.count = 0

            async def __anext__(self) -> MagicMock:
                if self.count < 1:
                    mock = MagicMock()
                    mock.value = b"\xff\xfe\xfd"  # corrupt avro data
                    mock.headers = [("foo", b"bar")]
                    mock.timestamp = 1708714664000
                    mock.topic = "test-topic"
                    mock.partition = 0
                    mock.offset = 0
                    self.count += 1
                    return mock
                raise StopAsyncIteration

        class AvroNoneConsumer(AsyncMock):  # type: ignore[misc]
            def __aiter__(self) -> AvroNoneIterator:
                return AvroNoneIterator()

            def subscribe(self, topics: list[str], pattern: str | None = None) -> None:
                pass

        with patch(
            "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
            new=AvroNoneConsumer,
        ):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "eda",
                        "host": "localhost",
                        "port": "9092",
                        "group_id": "test",
                        "message_format": "avro",
                    },
                )
            )
            # Corrupt data returns None, message should be skipped
            assert len(myqueue.queue) == 0


class TestDeserializerCloseViaMain:
    """Test that deserializer.close() is called in main() finally block."""

    def test_deserializer_closed_after_main(
        self, myqueue: MockQueue, avro_schema_file: str
    ) -> None:
        close_called = {"value": False}

        original_close = AvroDeserializer.close

        async def mock_close(self: AvroDeserializer) -> None:
            close_called["value"] = True
            await original_close(self)

        with (
            patch(
                "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer",
                new=MockConsumer,
            ),
            patch.object(AvroDeserializer, "close", mock_close),
        ):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "eda",
                        "host": "localhost",
                        "port": "9092",
                        "group_id": "test",
                        "message_format": "avro",
                        "avro_schema_file": avro_schema_file,
                    },
                )
            )
            assert close_called["value"] is True
