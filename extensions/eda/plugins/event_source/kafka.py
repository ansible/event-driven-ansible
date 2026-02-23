from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import TYPE_CHECKING, Any

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

if TYPE_CHECKING:
    from aiokafka.structs import ConsumerRecord

DOCUMENTATION = r"""
---
short_description: Receive events via a kafka topic.
description:
  - An ansible-rulebook event source plugin for receiving events via a kafka topic.
  - To make each message unique you can either add message_uuid to the header or
  - add message_uuid to the message body
  - if both of these are missing we will use the {topic}:{partition}.{offset} to
  - make the unique message uuid
options:
  host:
    description:
      - The host where the kafka topic is hosted.
    type: str
    required: true
  port:
    description:
      - The port where the kafka server is listening.
    type: str
    required: true
  cafile:
    description:
      - The optional certificate authority file path containing certificates
        used to sign kafka broker certificates
    type: str
  certfile:
    description:
      - The optional client certificate file path containing the client
        certificate, as well as CA certificates needed to establish
        the certificate's authenticity.
    type: str
  keyfile:
    description:
      - The optional client key file path containing the client private key.
    type: str
  password:
    description:
      - The optional password to be used when loading the certificate chain.
    type: str
  check_hostname:
    description:
      - Enable SSL hostname verification.
    type: bool
    default: true
  verify_mode:
    description:
      - Whether to try to verify other peers' certificates and how to
        behave if verification fails.
    type: str
    default: "CERT_REQUIRED"
    choices: ["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"]
  encoding:
    description:
      - Message encoding scheme.
    type: str
    default: "utf-8"
  topic:
    description:
      - The kafka topic. topic, topics, and topic_pattern are mutually exclusive.
    type: str
  topics:
    description:
      - The kafka topics. topic, topics, and topic_pattern are mutually exclusive.
    type: list
    elements: str
  topic_pattern:
    description:
      - The kafka topic pattern. It must be a valid regex. topic, topics, and topic_pattern are mutually exclusive.
        [AIOKafkaConsumer](https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.AIOKafkaConsumer) performs
        periodic metadata refreshes in the background and will notice when new partitions are added to one of the
        subscribed topics or when a new topic matching a subscribed regex is created. See metadata_max_age_ms for
        more details on how to configure the metadata refresh.
    type: str
  metadata_max_age_ms:
    description:
      - The period of time in milliseconds for forcing a refresh of metadata.
        It configures how soon a topic or partition change is detected. Default to 5 minutes.
    type: int
    default: 300000 # 5 minutes
  group_id:
    description:
      - A kafka group id.
    type: str
    default: null
  offset:
    description:
      - Where to automatically reset the offset.
    type: str
    default: "latest"
    choices: ["latest", "earliest"]
  security_protocol:
    description:
      - Protocol used to communicate with brokers.
    type: str
    default: "PLAINTEXT"
    choices: ["PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"]
  sasl_mechanism:
    description:
      - Authentication mechanism when security_protocol is configured.
    type: str
    default: "PLAIN"
    choices: ["PLAIN", "GSSAPI", "SCRAM-SHA-256", "SCRAM-SHA-512", "OAUTHBEARER"]
  sasl_plain_username:
    description:
      - Username for SASL PLAIN authentication.
    type: str
  sasl_plain_password:
    description:
      - Password for SASL PLAIN authentication.
    type: str
  sasl_kerberos_service_name:
    description:
      - The service name, default is kafka
    type: str
  sasl_kerberos_domain_name:
    description:
      - The kerberos REALM
    type: str
  feedback:
    type: bool
    default: false
    description:
      - Should the source plugin wait for feedback before
      - processing the next event from the kafka topic
      - This flag allows ansible rulebook to pass in an asyncio
      - queue which is passed in the args['eda_feedback_queue']
      - The source plugin should wait for the response to come
      - back on this queue before it picks the next event from
      - Kafka topic.
"""

EXAMPLES = r"""
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    check_hostname: true
    verify_mode: "CERT_OPTIONAL"
    encoding: "utf-8"
    topics:
      - "demo"
      - "demo2"
    group_id: "test"
    offset: "earliest"
    security_protocol: "SASL_PLAINTEXT"
    sasl_mechanism: "GSSAPI"
    sasl_plain_username: "admin"
    sasl_plain_password: "test"
"""

MESSAGE_UUID_KEY = "message_uuid"
QUEUE_TIMEOUT = 120


def _validate_and_normalize_topics(args: dict[str, Any]) -> list[str] | None:
    """Validate and normalize topic configuration.

    Args:
        args: Plugin arguments

    Returns:
        List of topics or None if topic_pattern is used

    Raises:
        ValueError: If topic configuration is invalid

    """
    topic = args.get("topic")
    topics = args.get("topics")
    topic_pattern = args.get("topic_pattern")

    num_topics = sum(1 for tp in (topic, topics, topic_pattern) if tp is not None)
    if num_topics != 1:
        msg = "Exactly one of topic, topics, or topic_pattern must be provided."
        raise ValueError(msg)

    if topic:
        return [topic]
    return topics


def _parse_kafka_args(args: dict[str, Any]) -> dict[str, Any]:
    """Parse and extract Kafka configuration from args.

    Args:
        args: Plugin arguments

    Returns:
        Dictionary containing parsed Kafka configuration

    Raises:
        ValueError: If offset is invalid

    """
    offset = args.get("offset", "latest")
    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    feedback_enabled = args.get("feedback", False)
    enable_auto_commit = True
    eda_feedback_queue = None

    if args.get("eda_feedback_queue"):
        enable_auto_commit = False
        eda_feedback_queue = args.get("eda_feedback_queue")

    if feedback_enabled and eda_feedback_queue is None:
        msg = (
            "feedback: true was set but no feedback queue was provided. "
            "This requires a compatible version of ansible-rulebook that "
            "supports the feedback mechanism."
        )
        raise ValueError(msg)

    return {
        "host": args.get("host"),
        "port": args.get("port"),
        "cafile": args.get("cafile"),
        "certfile": args.get("certfile"),
        "keyfile": args.get("keyfile"),
        "password": args.get("password"),
        "check_hostname": args.get("check_hostname", True),
        "verify_mode": args.get("verify_mode", "CERT_REQUIRED"),
        "group_id": args.get("group_id"),
        "offset": offset,
        "encoding": args.get("encoding", "utf-8"),
        "security_protocol": args.get("security_protocol", "PLAINTEXT"),
        "enable_auto_commit": enable_auto_commit,
        "eda_feedback_queue": eda_feedback_queue,
        "sasl_mechanism": args.get("sasl_mechanism", "PLAIN"),
        "sasl_plain_username": args.get("sasl_plain_username"),
        "sasl_plain_password": args.get("sasl_plain_password"),
        "sasl_kerberos_service_name": args.get("sasl_kerberos_service_name"),
        "sasl_kerberos_domain_name": args.get("sasl_kerberos_domain_name"),
        "metadata_max_age_ms": int(args.get("metadata_max_age_ms", 300000)),
    }


def _create_ssl_context(
    cafile: str | None,
    certfile: str | None,
    keyfile: str | None,
    password: str | None,
    *,
    check_hostname: bool,
    verify_mode_str: str,
    security_protocol: str,
) -> tuple[Any | None, str]:
    """Create SSL context if needed.

    Args:
        cafile: CA file path
        certfile: Certificate file path
        keyfile: Key file path
        password: Password for the key file
        check_hostname: Whether to check hostname
        verify_mode_str: Verification mode string
        security_protocol: Security protocol

    Returns:
        Tuple of (ssl_context, updated_security_protocol)

    Raises:
        ValueError: If verify_mode is invalid

    """
    verify_modes = {
        "CERT_NONE": CERT_NONE,
        "CERT_OPTIONAL": CERT_OPTIONAL,
        "CERT_REQUIRED": CERT_REQUIRED,
    }
    try:
        verify_mode = verify_modes[verify_mode_str]
    except KeyError as exc:
        msg = f"Invalid verify_mode option: {verify_mode_str}"
        raise ValueError(msg) from exc

    if not (cafile or security_protocol.endswith("SSL")):
        return None, security_protocol

    security_protocol = security_protocol.replace("PLAINTEXT", "SSL")
    ssl_context = create_ssl_context(
        cafile=cafile,
        certfile=certfile,
        keyfile=keyfile,
        password=password,
    )
    ssl_context.check_hostname = check_hostname
    ssl_context.verify_mode = verify_mode
    return ssl_context, security_protocol


def get_message_timestamp(msg: ConsumerRecord) -> str:
    """Convert Kafka message timestamp to ISO 8601 format with Z suffix.

    Args:
        msg: Kafka ConsumerRecord containing timestamp in milliseconds

    Returns:
        ISO 8601 formatted timestamp string with Z suffix (e.g., "2024-02-23T18:57:44Z")

    """
    return (
        datetime.fromtimestamp(msg.timestamp / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


async def main(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
    logger = logging.getLogger()

    # Validate and normalize topics
    topics = _validate_and_normalize_topics(args)
    topic_pattern = args.get("topic_pattern")

    # Parse Kafka configuration
    config = _parse_kafka_args(args)

    # Create SSL context if needed
    ssl_context, security_protocol = _create_ssl_context(
        cafile=config["cafile"],
        certfile=config["certfile"],
        keyfile=config["keyfile"],
        password=config["password"],
        check_hostname=config["check_hostname"],
        verify_mode_str=config["verify_mode"],
        security_protocol=config["security_protocol"],
    )

    # Create Kafka consumer
    kafka_consumer = AIOKafkaConsumer(
        bootstrap_servers=f"{config['host']}:{config['port']}",
        group_id=config["group_id"],
        enable_auto_commit=config["enable_auto_commit"],
        max_poll_records=1,
        auto_offset_reset=config["offset"],
        security_protocol=security_protocol,
        ssl_context=ssl_context,
        sasl_mechanism=config["sasl_mechanism"],
        sasl_plain_username=config["sasl_plain_username"],
        sasl_plain_password=config["sasl_plain_password"],
        sasl_kerberos_service_name=config["sasl_kerberos_service_name"],
        sasl_kerberos_domain_name=config["sasl_kerberos_domain_name"],
        metadata_max_age_ms=config["metadata_max_age_ms"],
    )

    kafka_consumer.subscribe(topics=topics, pattern=topic_pattern)

    await kafka_consumer.start()

    try:
        await receive_msg(
            queue,
            kafka_consumer,
            config["encoding"],
            config["eda_feedback_queue"],
        )
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()


async def receive_msg(
    queue: asyncio.Queue[Any],
    kafka_consumer: AIOKafkaConsumer,
    encoding: str,
    eda_feedback_queue: asyncio.Queue[Any] | None,
) -> None:
    """Receive messages from the Kafka topic and put them into the queue."""
    logger = logging.getLogger()

    async for msg in kafka_consumer:
        event: dict[str, Any] = {}

        # Process headers
        try:
            headers: dict[str, str] = {
                header[0]: header[1].decode(encoding) for header in msg.headers
            }
            event["meta"] = {}
            event["meta"]["headers"] = headers
            if MESSAGE_UUID_KEY in headers:
                event["meta"]["uuid"] = headers[MESSAGE_UUID_KEY]
            else:
                event["meta"]["uuid"] = f"{msg.topic}:{msg.partition}:{msg.offset}"
            event["meta"]["produced_at"] = get_message_timestamp(msg)

        except UnicodeError:
            logger.exception("Unicode error while decoding headers")

        # Process message body
        try:
            value = msg.value.decode(encoding)
            data = json.loads(value)
        except json.decoder.JSONDecodeError:
            logger.info("JSON decode error, storing raw value")
            data = value
        except UnicodeError:
            logger.exception("Unicode error while decoding message body")
            data = None

        # Add data to the event and put it into the queue
        if data:
            if MESSAGE_UUID_KEY in data:
                event["meta"]["uuid"] = data[MESSAGE_UUID_KEY]

            event["body"] = data
            await queue.put(event)
            if eda_feedback_queue:
                try:
                    await asyncio.wait_for(
                        eda_feedback_queue.get(), timeout=QUEUE_TIMEOUT
                    )
                    await kafka_consumer.commit()
                except asyncio.TimeoutError:
                    logger.exception("Timed out waiting for feedback")

        await asyncio.sleep(0)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: MockQueue, event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"},
        ),
    )
