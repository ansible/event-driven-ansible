# Kafka Integration Tests — Local Setup Guide

The Kafka integration tests are **automatically skipped on macOS and ARM64** in CI
because the test Kafka deployment uses x86_64 container images. This guide explains
how to run them locally on macOS for development.

Why we still use Confluent containers in CI: The existing integration tests test SSL, SASL_PLAINTEXT, and SASL_SSL security protocols — the Confluent image comes pre-configured with those listeners and JAAS auth. The broker_jaas.conf, keystore, and truststore files in the test directory are set up specifically for the Confluent image. Migrating to the Apache image would require reconfiguring all of that.

## Prerequisites

- **Podman Desktop** (or Docker Desktop) with `podman-compose` (or `docker-compose`)
- **Python 3.9+** with the project venv activated
- **ansible-rulebook** installed
- **fastavro** installed (for Avro tests)

## Option 1: Run Tests via Podman on macOS

### 1. Install podman-compose

```bash
brew install podman-compose
# Or: pip install podman-compose
```

### 2. Start the Kafka Broker

```bash
cd tests/integration/event_source_kafka

# Generate SSL certs for the broker
./certs-create.sh

# Start Kafka + ZooKeeper
podman-compose up -d

# Wait for readiness
podman-compose logs -f broker 2>&1 | grep -m1 "started"
```

### 3. Run the Integration Tests

The tests skip on macOS by default. To override, temporarily modify
`should_skip_kafka_tests()` in `test_kafka_source.py`, or run with a
pytest marker override:

```bash
# From the collection root:
python -m pytest tests/integration/event_source_kafka/test_kafka_source.py -v -k "plaintext or avro" -s
```

> **Note:** If `should_skip_kafka_tests()` returns `True`, all tests will
> be skipped. For local dev, you can set an env var override:
>
> ```python
> # In test_kafka_source.py, modify should_skip_kafka_tests():
> def should_skip_kafka_tests() -> bool:
>     if os.environ.get("FORCE_KAFKA_TESTS"):
>         return False
>     # ... rest of function
> ```
>
> Then run with: `FORCE_KAFKA_TESTS=1 python -m pytest ...`

### 4. Clean Up

```bash
cd tests/integration/event_source_kafka
podman-compose down -v
./certs-clean.sh
```

## Option 2: Run Avro Tests Standalone (No Kafka Broker)

If you only want to validate Avro deserialization logic without a live Kafka
broker, the **unit tests** cover all Avro paths:

```bash
# From the collection root:
python -m pytest tests/unit/event_source/test_kafka.py -v -k "Avro"
```

This runs 14 Avro-specific tests covering:
- Schema file loading and validation
- Schemaless deserialization with local `.avsc` files
- Object Container format (self-describing)
- Error handling (corrupt data, size limits, missing fastavro)
- Full `main()` flow with mocked Kafka consumer

## Option 3: Manual End-to-End Test with Avro

For a hands-on test without the test framework:

### 1. Start a KRaft Kafka Broker

```bash
podman run -d \
  --name kafka-avro-test \
  -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
  -e KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 \
  apache/kafka:latest
```

### 2. Create a Topic

```bash
podman exec kafka-avro-test \
  /opt/kafka/bin/kafka-topics.sh \
  --create --topic avro-alerts \
  --partitions 1 --replication-factor 1 \
  --bootstrap-server localhost:9092
```

### 3. Produce Avro Messages

```python
#!/usr/bin/env python3
"""produce_avro_test.py — Send Avro messages to Kafka for manual testing."""

import asyncio
import io
import json

import fastavro
from aiokafka import AIOKafkaProducer

SCHEMA = {
    "type": "record",
    "name": "TestEvent",
    "namespace": "com.example.eda.test",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "value", "type": "int"},
    ],
}

async def produce():
    parsed = fastavro.parse_schema(SCHEMA)
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()
    try:
        for record in [
            {"name": "test-alert", "value": 42},
            {"name": "stop", "value": 0},
        ]:
            buf = io.BytesIO()
            fastavro.schemaless_writer(buf, parsed, record)
            await producer.send_and_wait("avro-alerts", buf.getvalue())
            print(f"Sent: {record}")
    finally:
        await producer.stop()

asyncio.run(produce())
```

### 4. Create a Rulebook

```yaml
# avro-test-rulebook.yml
---
- name: Avro Test
  hosts: localhost
  sources:
    - ansible.eda.kafka:
        host: localhost
        port: "9092"
        topic: avro-alerts
        offset: earliest
        message_format: avro
        avro_schema_file: /path/to/test_event.avsc
  rules:
    - name: match event
      condition: event.body.name == "test-alert"
      action:
        debug:
          msg: "Got Avro event: {{ event.body }}"
    - name: stop
      condition: event.body.name == "stop"
      action:
        shutdown:
```

### 5. Run

```bash
# Terminal 1: Start rulebook
ansible-rulebook --rulebook avro-test-rulebook.yml \
                 --inventory inventory.yml --verbose

# Terminal 2: Produce messages
python3 produce_avro_test.py
```

### 6. Clean Up

```bash
podman rm -f kafka-avro-test
```
