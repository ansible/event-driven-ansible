import json
import os
import subprocess

import pytest
from kafka import KafkaProducer

from ..utils import TESTS_PATH, CLIRunner


@pytest.fixture()
def kafka_broker():
    cwd = os.path.join(TESTS_PATH, "event_source_kafka")
    print(cwd)
    result = subprocess.run(["docker-compose", "up", "-d"], cwd=cwd, check=True)
    yield result
    subprocess.run(["docker-compose", "down", "-v"], cwd=cwd, check=True)


@pytest.fixture()
def kafka_producer(kafka_broker):
    return KafkaProducer(bootstrap_servers="localhost:9092")


def test_kafka_source_sanity(kafka_producer: KafkaProducer):
    ruleset = os.path.join(TESTS_PATH, "event_source_kafka", "test_kafka_rules.yml")

    msgs = [
        json.dumps({"name": "some kafka event"}).encode("ascii"),
        json.dumps({"name": "stop"}).encode("ascii"),
    ]

    for msg in msgs:
        kafka_producer.send(topic="kafka-events", value=msg)

    result = CLIRunner(rules=ruleset).run()

    assert "Rule fired successfully" in result.stdout.decode()
