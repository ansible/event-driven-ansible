import pytest
import os
import subprocess
from kafka import KafkaProducer
import json
from ..utils import CLIRunner, TESTS_PATH


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

    assert "'msg': 'SUCCESS'" in result.stdout.decode()
