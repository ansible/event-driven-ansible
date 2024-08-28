"""kafka.py.

An ansible-rulebook event source plugin for receiving events via a kafka topic.

Arguments:
---------
    host:      The host where the kafka topic is hosted
    port:      The port where the kafka server is listening
    cafile:    The optional certificate authority file path containing certificates
               used to sign kafka broker certificates
    certfile:  The optional client certificate file path containing the client
               certificate, as well as CA certificates needed to establish
               the certificate's authenticity
    keyfile:   The optional client key file path containing the client private key
    password:  The optional password to be used when loading the certificate chain
    check_hostname:  Enable SSL hostname verification. [True (default), False]
    verify_mode: Whether to try to verify other peers' certificates and how to
               behave if verification fails. [CERT_NONE, CERT_OPTIONAL,
               CERT_REQUIRED (default)]
    encoding:  Message encoding scheme. Default to utf-8
    topic:     The kafka topic
    group_id:  A kafka group id
    offset:    Where to automatically reset the offset. [latest, earliest]
               Default to latest
    security_protocol: Protocol used to communicate with brokers. [PLAINTEXT, SSL,
               SASL_PLAINTEXT, SASL_SSL]. Default to PLAINTEXT
    sasl_mechanism: Authentication mechanism when security_protocol is configured.
               [PLAIN, GSSAPI, SCRAM-SHA-256, SCRAM-SHA-512, OAUTHBEARER].
               Default to PLAIN.
    sasl_plain_username: Username for SASL PLAIN authentication
    sasl_plain_password: Password for SASL PLAIN authentication



"""

import asyncio
import json
import logging
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context


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
    group_id = args.get("group_id", None)
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
