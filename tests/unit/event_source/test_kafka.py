from __future__ import annotations

import asyncio
import json
import secrets
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from asyncmock import AsyncMock

from extensions.eda.plugins.event_source.kafka import SUPPORTED_SASL_MECHANISMS
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
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Set up default return values for async methods
        self.start = AsyncMock()
        self.stop = AsyncMock()

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
                    "port": "9092",
                    "group_id": "test",
                    "sasl_plain_username": "fred",
                    "sasl_plain_password": secrets.token_hex(),
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


# Tests for SASL mechanism validation
class TestSASLMechanismValidation:
    """Tests for SASL mechanism validation."""

    def test_supported_sasl_mechanisms_includes_oauthbearer(self) -> None:
        """Test that OAUTHBEARER is included in supported mechanisms."""
        assert "OAUTHBEARER" in SUPPORTED_SASL_MECHANISMS
        expected_mechanisms = [
            "PLAIN",
            "SCRAM-SHA-256",
            "SCRAM-SHA-512",
            "GSSAPI",
            "OAUTHBEARER",
        ]
        assert SUPPORTED_SASL_MECHANISMS == expected_mechanisms

    def test_unsupported_sasl_mechanism_raises_error(self, myqueue: MockQueue) -> None:
        """Test that unsupported SASL mechanism raises ValueError."""
        with pytest.raises(ValueError, match="SASL Mechanism INVALID is not supported"):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "test",
                        "host": "localhost",
                        "port": "9092",
                        "sasl_mechanism": "INVALID",
                    },
                )
            )


# Tests for OAuth integration changes
class TestOAuthIntegration:
    """Tests for OAuth token provider integration in Kafka consumer."""

    @patch("oauth_tokens.create_oauth_provider")
    @patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer", new=MockConsumer
    )
    def test_oauthbearer_creates_token_provider(
        self, mock_create_oauth_provider: MagicMock, myqueue: MockQueue
    ) -> None:
        """Test that OAUTHBEARER mechanism creates OAuth token provider."""
        mock_token_provider = MagicMock()
        mock_create_oauth_provider.return_value = mock_token_provider

        args = {
            "topic": "test",
            "host": "localhost",
            "port": "9092",
            "sasl_mechanism": "OAUTHBEARER",
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }

        asyncio.run(kafka_main(myqueue, args))

        # Verify create_oauth_provider was called with the args
        mock_create_oauth_provider.assert_called_once_with(args)

    @patch("oauth_tokens.create_oauth_provider")
    @patch("extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer")
    def test_oauth_token_provider_passed_to_consumer(
        self,
        mock_consumer_class: MagicMock,
        mock_create_oauth_provider: MagicMock,
        myqueue: MockQueue,
    ) -> None:
        """Test that OAuth token provider is passed to AIOKafkaConsumer."""
        mock_token_provider = MagicMock()
        mock_create_oauth_provider.return_value = mock_token_provider

        # Create a mock consumer that properly implements the async iterator protocol
        mock_consumer = MockConsumer()
        mock_consumer_class.return_value = mock_consumer

        args = {
            "topic": "test",
            "host": "localhost",
            "port": "9092",
            "sasl_mechanism": "OAUTHBEARER",
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }

        asyncio.run(kafka_main(myqueue, args))

        # Verify AIOKafkaConsumer was called with the token provider
        mock_consumer_class.assert_called_once()
        call_kwargs = mock_consumer_class.call_args[1]
        assert call_kwargs["sasl_oauth_token_provider"] == mock_token_provider

    @patch(
        "extensions.eda.plugins.event_source.kafka.AIOKafkaConsumer", new=MockConsumer
    )
    def test_non_oauthbearer_mechanism_no_token_provider(
        self, myqueue: MockQueue
    ) -> None:
        """Test that non-OAUTHBEARER mechanisms don't create token provider."""
        args = {
            "topic": "test",
            "host": "localhost",
            "port": "9092",
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": "user",
            "sasl_plain_password": "pass",
        }

        # This should not raise any OAuth-related errors
        asyncio.run(kafka_main(myqueue, args))

    @patch("oauth_tokens.create_oauth_provider")
    def test_oauth_provider_creation_error_propagated(
        self, mock_create_oauth_provider: MagicMock, myqueue: MockQueue
    ) -> None:
        """Test that OAuth provider creation errors are propagated."""
        mock_create_oauth_provider.side_effect = ValueError(
            "Invalid OAuth configuration"
        )

        with pytest.raises(ValueError, match="Invalid OAuth configuration"):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "test",
                        "host": "localhost",
                        "port": "9092",
                        "sasl_mechanism": "OAUTHBEARER",
                        "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                        "sasl_oauth_client_id": "test-client",
                        # Missing required OAuth parameters
                    },
                )
            )


# Tests for PLAIN mechanism credential validation
class TestPlainMechanismValidation:
    """Tests for PLAIN mechanism credential validation."""

    def test_plain_mechanism_missing_credentials_raises_error(
        self, myqueue: MockQueue
    ) -> None:
        """Test that PLAIN mechanism without credentials raises ValueError."""
        with pytest.raises(
            ValueError,
            match=(
                "For sasl_mechanism PLAIN.*is missing.*Please specify "
                "all of the following arguments.*sasl_plain_username."
                "*sasl_plain_password"
            ),
        ):
            asyncio.run(
                kafka_main(
                    myqueue,
                    {
                        "topic": "test",
                        "host": "localhost",
                        "port": "9092",
                        "sasl_mechanism": "PLAIN",
                        # Missing sasl_plain_username and sasl_plain_password
                    },
                )
            )


# Tests for SCRAM mechanism credential validation
class TestScramMechanismValidation:
    """Tests for SCRAM mechanism credential validation."""

    def test_scram_mechanism_missing_credentials_raises_error(
        self, myqueue: MockQueue
    ) -> None:
        """Test that SCRAM mechanisms without credentials raise ValueError."""
        for mechanism in ["SCRAM-SHA-256", "SCRAM-SHA-512"]:
            with pytest.raises(
                ValueError,
                match=(
                    f"For sasl_mechanism {mechanism}.*is missing.*Please "
                    "specify all of the following arguments.*sasl_plain_username."
                    "*sasl_plain_password"
                ),
            ):
                asyncio.run(
                    kafka_main(
                        myqueue,
                        {
                            "topic": "test",
                            "host": "localhost",
                            "port": "9092",
                            "sasl_mechanism": mechanism,
                            # Missing credentials
                        },
                    )
                )
