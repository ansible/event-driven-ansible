import json
import os
import subprocess

import pytest
from kafka import KafkaProducer

from ..utils import TESTS_PATH, CLIRunner


@pytest.fixture(scope="session")
def kafka_certs():
    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    result = subprocess.run([os.path.join(cwd, "certs-create.sh")], cwd=cwd, check=True)
    yield result
    subprocess.run([os.path.join(cwd, "certs-clean.sh")], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_broker():
    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    result = subprocess.run(["docker-compose", "up", "-d"], cwd=cwd, check=True)
    yield result
    subprocess.run(["docker-compose", "down", "-v"], cwd=cwd, check=True)


@pytest.fixture(scope="session")
def kafka_producer(kafka_certs, kafka_broker):
    return KafkaProducer(bootstrap_servers="localhost:9092")


def test_kafka_source_plaintext(kafka_certs, kafka_broker, kafka_producer):
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_plaintext.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for PLAINTEXT consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    for msg in msgs:
        kafka_producer.send(topic="kafka-events-plaintext", value=msg)

    result = CLIRunner(rules=ruleset).run()

    assert "Rule fired successfully for PLAINTEXT consumers" in result.stdout.decode()


def test_kafka_source_ssl(kafka_certs, kafka_broker, kafka_producer):
    ruleset = os.path.join(TESTS_PATH, "event_source_kafka", "test_kafka_rules_ssl.yml")

    msgs = [
        json.dumps({"name": "Produced for SSL consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    for msg in msgs:
        kafka_producer.send(topic="kafka-events-ssl", value=msg)

    result = CLIRunner(rules=ruleset).run()

    assert "Rule fired successfully for SSL consumers" in result.stdout.decode()


def test_kafka_source_sasl_plaintext(kafka_certs, kafka_broker, kafka_producer):
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_plaintext.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for SASL_PLAINTEXT consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    for msg in msgs:
        kafka_producer.send(topic="kafka-events-sasl-plaintext", value=msg)

    result = CLIRunner(rules=ruleset).run()

    assert (
        "Rule fired successfully for SASL_PLAINTEXT consumers" in result.stdout.decode()
    )


def test_kafka_source_sasl_ssl(kafka_certs, kafka_broker, kafka_producer):
    ruleset = os.path.join(
        TESTS_PATH, "event_source_kafka", "test_kafka_rules_sasl_ssl.yml"
    )

    msgs = [
        json.dumps({"name": "Produced for SASL_SSL consumers"}).encode("ascii"),
        "stop".encode("ascii"),
    ]

    for msg in msgs:
        kafka_producer.send(topic="kafka-events-sasl-ssl", value=msg)

    result = CLIRunner(rules=ruleset).run()

    assert "Rule fired successfully for SASL_SSL consumers" in result.stdout.decode()
