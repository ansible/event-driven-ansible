import json
import os
import platform
import re
import subprocess
from typing import Any, Generator, Optional

import pytest
from kafka import KafkaProducer

from .. import TESTS_PATH
from ..utils import CLIRunner, wait_for_kafka_ready


def should_skip_kafka_tests() -> bool:
    """
    Determine if Kafka tests should be skipped based on platform.

    Do not run kafka tests on macos or arm64 because the testing kafka deployment does
    not run on arm64 and macos does not provide podman-compose cli.

    Returns:
        bool: True if tests should be skipped, False otherwise
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Check for macos
    if system == "darwin":
        return True

    # Check for arm64
    if machine == "aarch64":
        return True

    return False


IS_UNAVAILABLE_PLATFORM=should_skip_kafka_tests()
SKIP_REASON = "Skipping Kafka tests on macos or arm64"


def send_kafka_messages_and_run_test(
    kafka_producer: KafkaProducer,
    topics_and_messages: list[tuple[str, bytes]],
    ruleset: str,
    expected_output_pattern: str,
    expected_match_count: int = 1,
    headers: Optional[list[tuple[str, bytes]]] = None,
) -> None:
    """
    Helper function to send Kafka messages and run tests with improved reliability.

    Args:
        kafka_producer: Kafka producer instance
        topics_and_messages: List of (topic, message) tuples to send
        ruleset: Path to rulebook file
        expected_output_pattern: Regex pattern to match in output
        expected_match_count: Expected number of pattern matches in output
        headers: Optional headers to send with all messages (except stop messages)
    """
    # Send messages with proper flushing
    for topic, message in topics_and_messages:
        # Only send headers with non-stop messages to avoid interfering with shutdown
        if headers and message != b"stop":
            kafka_producer.send(topic=topic, value=message, headers=headers)
        else:
            kafka_producer.send(topic=topic, value=message)

    # Ensure all messages are sent before proceeding
    kafka_producer.flush()

    # Run the rulebook test
    result = CLIRunner(rules=ruleset).run()

    # Use pattern matching for more robust output checking
    stdout_content = result.stdout.decode()

    # Count the number of matches
    matches = len(re.findall(expected_output_pattern, stdout_content, re.IGNORECASE))
    mismatch_msg = (
        f"Expected {expected_match_count} matches of pattern '{expected_output_pattern}', "
        f"found {matches}. Output: {stdout_content}"
    )
    assert matches == expected_match_count, mismatch_msg


@pytest.fixture(scope="session")
def kafka_certs() -> Generator[subprocess.CompletedProcess[bytes], None, None]:
    if IS_UNAVAILABLE_PLATFORM:
        pytest.skip(SKIP_REASON)

    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    result = subprocess.run([os.path.join(cwd, "certs-create.sh")], cwd=cwd, check=True)
    yield result
    subprocess.run([os.path.join(cwd, "certs-clean.sh")], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_broker() -> Generator[subprocess.CompletedProcess[bytes], None, None]:
    if IS_UNAVAILABLE_PLATFORM:
        pytest.skip(SKIP_REASON)

    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    # Keep --quiet-pull here is it does spam CI/CD console
    result = subprocess.run(
        ["podman-compose", "up", "--quiet-pull", "-d"], cwd=cwd, check=True
    )

    # Wait for Kafka broker to be ready - focus on main port first
    wait_for_kafka_ready("localhost:9092", timeout=30)  # PLAINTEXT - main port

    # Check SSL/SASL ports are listening (but don't require full producer setup)
    wait_for_kafka_ready("localhost:9093", timeout=15, check_ssl=True)  # SSL
    wait_for_kafka_ready("localhost:9094", timeout=15, check_ssl=True)  # SASL_PLAINTEXT
    wait_for_kafka_ready("localhost:9095", timeout=15, check_ssl=True)  # SASL_SSL

    yield result
    subprocess.run(["podman-compose", "down", "-v"], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_producer(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
) -> KafkaProducer:
    if IS_UNAVAILABLE_PLATFORM:
        pytest.skip(SKIP_REASON)

    return KafkaProducer(bootstrap_servers="localhost:9092")


def test_kafka_source_plaintext(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_plaintext.yml"
    )

    topics_and_messages = [
        ("kafka-events-plaintext", json.dumps({"name": "Produced for PLAINTEXT consumers"}).encode("ascii")),
        ("kafka-events-plaintext", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*PLAINTEXT consumers",
        expected_match_count=1,
    )


def test_kafka_source_with_headers(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_headers.yml"
    )

    topics_and_messages = [
        ("kafka-events-plaintext", json.dumps({"name": "Produced for PLAINTEXT consumers"}).encode("ascii")),
        ("kafka-events-plaintext", "stop".encode("ascii")),
    ]

    headers = [
        (key, value.encode("ascii"))
        for key, value in json.loads('{"foo": "bar"}').items()
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*headers",
        expected_match_count=1,
        headers=headers,
    )


def test_kafka_source_ssl(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(TESTS_PATH, "event_source_kafka", "test_kafka_rules_ssl.yml")

    topics_and_messages = [
        ("kafka-events-ssl", json.dumps({"name": "Produced for SSL consumers"}).encode("ascii")),
        ("kafka-events-ssl", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SSL consumers",
        expected_match_count=1,
    )


def test_kafka_source_sasl_plaintext(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_plaintext.yml"
    )

    topics_and_messages = [
        ("kafka-events-sasl-plaintext", json.dumps({"name": "Produced for SASL_PLAINTEXT consumers"}).encode("ascii")),
        ("kafka-events-sasl-plaintext", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SASL_PLAINTEXT consumers",
        expected_match_count=1,
    )


def test_kafka_source_sasl_ssl(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_ssl.yml"
    )

    topics_and_messages = [
        ("kafka-events-sasl-ssl", json.dumps({"name": "Produced for SASL_SSL consumers"}).encode("ascii")),
        ("kafka-events-sasl-ssl", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SASL_SSL consumers",
        expected_match_count=1,
    )


def test_kafka_source_multiple_topics(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    """Test Kafka source with multiple topics exact matching."""
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_multiple_topics.yml"
    )

    # Send messages to different topics - should get 2 rule matches
    topics_and_messages = [
        ("kafka-events-topic1", json.dumps({"name": "Multi-topic test"}).encode("ascii")),
        ("kafka-events-topic2", json.dumps({"name": "Multi-topic test"}).encode("ascii")),
        ("kafka-events-other", json.dumps({"name": "Other topic"}).encode("ascii")),
        ("kafka-events-topic1", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully for multiple topics",
        expected_match_count=2,
    )


def test_kafka_source_pattern_topics(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    """Test Kafka source with topic pattern matching."""
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_pattern_topics.yml"
    )

    # Send messages to topics matching the pattern "kafka-pattern-.*" - should get 3 rule matches
    topics_and_messages = [
        ("kafka-pattern-alpha", json.dumps({"name": "Pattern test"}).encode("ascii")),
        ("kafka-pattern-beta", json.dumps({"name": "Pattern test"}).encode("ascii")),
        ("kafka-pattern-gamma", json.dumps({"name": "Pattern test"}).encode("ascii")),
        ("kafka-non-pattern", json.dumps({"name": "Pattern test"}).encode("ascii")),
        ("kafka-pattern-alpha", "stop".encode("ascii")),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topics_and_messages=topics_and_messages,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully for pattern topics",
        expected_match_count=3,
    )
