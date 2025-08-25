import json
import os
import re
import subprocess
import time
from typing import Any, Generator

import pytest
from kafka import KafkaProducer

from .. import TESTS_PATH
from ..utils import CLIRunner, wait_for_kafka_ready


def send_kafka_messages_and_run_test(
    kafka_producer: KafkaProducer,
    topic: str,
    messages: list[str],
    ruleset: str,
    expected_output_pattern: str,
) -> None:
    """
    Helper function to send Kafka messages and run tests with improved reliability.

    Args:
        kafka_producer: Kafka producer instance
        topic: Topic to send messages to
        messages: List of messages to send
        ruleset: Path to rulebook file
        expected_output_pattern: Regex pattern to match in output
    """
    # Send messages with proper flushing
    for msg in messages:
        kafka_producer.send(topic=topic, value=msg)

    # Ensure all messages are sent before proceeding
    kafka_producer.flush()
    print(f"Sent {len(messages)} messages to topic {topic}")

    # Brief pause to allow message propagation
    time.sleep(2)

    # Run the rulebook test
    result = CLIRunner(rules=ruleset).run()

    # Use pattern matching for more robust output checking
    stdout_content = result.stdout.decode()

    if not re.search(expected_output_pattern, stdout_content, re.IGNORECASE):
        print(f"Expected pattern: {expected_output_pattern}")
        print(f"Actual output: {stdout_content}")
        raise AssertionError(f"Expected pattern '{expected_output_pattern}' not found in output")

    print(f"✅ Test passed - Found expected pattern: {expected_output_pattern}")


@pytest.fixture(scope="session")
def kafka_certs() -> Generator[subprocess.CompletedProcess[bytes], None, None]:
    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    result = subprocess.run([os.path.join(cwd, "certs-create.sh")], cwd=cwd, check=True)
    yield result
    subprocess.run([os.path.join(cwd, "certs-clean.sh")], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_broker() -> Generator[subprocess.CompletedProcess[bytes], None, None]:
    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    # Keep --quiet-pull here is it does spam CI/CD console
    result = subprocess.run(
        ["docker-compose", "up", "--quiet-pull", "-d"], cwd=cwd, check=True
    )

    # Wait for Kafka broker to be ready - focus on main port first
    print("Waiting for Kafka brokers to be ready...")
    wait_for_kafka_ready("localhost:9092", timeout=30)  # PLAINTEXT - main port

    # Check SSL/SASL ports are listening (but don't require full producer setup)
    wait_for_kafka_ready("localhost:9093", timeout=15, check_ssl=True)  # SSL
    wait_for_kafka_ready("localhost:9094", timeout=15, check_ssl=True)  # SASL_PLAINTEXT
    wait_for_kafka_ready("localhost:9095", timeout=15, check_ssl=True)  # SASL_SSL
    print("All Kafka brokers are ready!")

    yield result
    subprocess.run(["docker-compose", "down", "-v"], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_producer(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
) -> KafkaProducer:
    return KafkaProducer(bootstrap_servers="localhost:9092")


def test_kafka_source_plaintext(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_plaintext.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for PLAINTEXT consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topic="kafka-events-plaintext",
        messages=msgs,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*PLAINTEXT consumers",
    )


def test_kafka_source_with_headers(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_headers.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for PLAINTEXT consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    headers = [
        (key, value.encode("ascii"))
        for key, value in json.loads('{"foo": "bar"}').items()
    ]

    # Send messages with headers using improved approach
    for msg in msgs:
        kafka_producer.send(topic="kafka-events-plaintext", value=msg, headers=headers)

    kafka_producer.flush()
    time.sleep(2)

    result = CLIRunner(rules=ruleset).run()
    stdout_content = result.stdout.decode()

    pattern = r"Rule fired successfully.*headers"
    if not re.search(pattern, stdout_content, re.IGNORECASE):
        print(f"Expected pattern: {pattern}")
        print(f"Actual output: {stdout_content}")
        raise AssertionError(f"Expected pattern '{pattern}' not found in output")

    print(f"✅ Test passed - Found expected pattern: {pattern}")


def test_kafka_source_ssl(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(TESTS_PATH, "event_source_kafka", "test_kafka_rules_ssl.yml")

    msgs = [
        json.dumps({"name": "Produced for SSL consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topic="kafka-events-ssl",
        messages=msgs,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SSL consumers",
    )


def test_kafka_source_sasl_plaintext(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_plaintext.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for SASL_PLAINTEXT consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topic="kafka-events-sasl-plaintext",
        messages=msgs,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SASL_PLAINTEXT consumers",
    )


def test_kafka_source_sasl_ssl(
    kafka_certs: subprocess.CompletedProcess[bytes],
    kafka_broker: subprocess.CompletedProcess[bytes],
    kafka_producer: Any,
) -> None:
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_ssl.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for SASL_SSL consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    send_kafka_messages_and_run_test(
        kafka_producer=kafka_producer,
        topic="kafka-events-sasl-ssl",
        messages=msgs,
        ruleset=ruleset,
        expected_output_pattern=r"Rule fired successfully.*SASL_SSL consumers",
    )
