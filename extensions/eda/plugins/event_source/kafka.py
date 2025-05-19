import asyncio
import json
import logging
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

DOCUMENTATION = r"""
---
short_description: Receive events via a kafka topic.
description:
  - An ansible-rulebook event source plugin for receiving events via a kafka topic.
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
      - The kafka topic.
    type: str
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
"""

EXAMPLES = r"""
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    check_hostname: true
    verify_mode: "CERT_OPTIONAL"
    encoding: "utf-8"
    topic: "demo"
    group_id: "test"
    offset: "earliest"
    security_protocol: "SASL_PLAINTEXT"
    sasl_mechanism: "GSSAPI"
    sasl_plain_username: "admin"
    sasl_plain_password: "test"
"""


async def main(  # pylint: disable=R0914
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
    logger = logging.getLogger()

    topic = args.get("topic")
    host = args.get("host")
    port = args.get("port")
    cafile = args.get("cafile")
    certfile = args.get("certfile")
    keyfile = args.get("keyfile")
    password = args.get("password")
    check_hostname = args.get("check_hostname", True)
    verify_mode = args.get("verify_mode", "CERT_REQUIRED")
    group_id = args.get("group_id")
    offset = args.get("offset", "latest")
    encoding = args.get("encoding", "utf-8")
    security_protocol = args.get("security_protocol", "PLAINTEXT")

    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    verify_modes = {
        "CERT_NONE": CERT_NONE,
        "CERT_OPTIONAL": CERT_OPTIONAL,
        "CERT_REQUIRED": CERT_REQUIRED,
    }
    try:
        verify_mode = verify_modes[verify_mode]
    except KeyError as exc:
        msg = f"Invalid verify_mode option: {verify_mode}"
        raise ValueError(msg) from exc

    ssl_context = None
    if cafile or security_protocol.endswith("SSL"):
        security_protocol = security_protocol.replace("PLAINTEXT", "SSL")
        ssl_context = create_ssl_context(
            cafile=cafile,
            certfile=certfile,
            keyfile=keyfile,
            password=password,
        )
        ssl_context.check_hostname = check_hostname
        ssl_context.verify_mode = verify_mode

    kafka_consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=f"{host}:{port}",
        group_id=group_id,
        enable_auto_commit=True,
        max_poll_records=1,
        auto_offset_reset=offset,
        security_protocol=security_protocol,
        ssl_context=ssl_context,
        sasl_mechanism=args.get("sasl_mechanism", "PLAIN"),
        sasl_plain_username=args.get("sasl_plain_username"),
        sasl_plain_password=args.get("sasl_plain_password"),
        sasl_kerberos_service_name=args.get("sasl_kerberos_service_name"),
        sasl_kerberos_domain_name=args.get("sasl_kerberos_domain_name"),
    )

    await kafka_consumer.start()

    try:
        await receive_msg(queue, kafka_consumer, encoding)
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()


async def receive_msg(
    queue: asyncio.Queue[Any],
    kafka_consumer: AIOKafkaConsumer,
    encoding: str,
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
            event["body"] = data
            await queue.put(event)

        await asyncio.sleep(0)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"},
        ),
    )
