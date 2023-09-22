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
    encoding:  Message encoding scheme. Default to utf-8
    topic:     The kafka topic
    group_id:  A kafka group id
    offset:    Where to automatically reset the offset. [latest, earliest]
               Default to latest
    security_protocol: Set Security protocol. See details in next point below.
    sasl_mechanism (str): Authentication mechanism when security_protocol
        is configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid values are:
        ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,
        ``OAUTHBEARER``.
        Default: ``PLAIN``
    sasl_plain_username (str): username for SASL ``PLAIN`` authentication.
        Default: None
    sasl_plain_password (str): password for SASL ``PLAIN`` authentication.


"""

import asyncio
import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context


async def main(  # pylint: disable=R0914
    queue: asyncio.Queue,
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
    logger = logging.getLogger()

# EXAMPLE for SCRAM
#    topic = "reviews.sentiment"
#    host = "kafka-kafka-bootstrap.globex-mw.svc.cluster.local"
#    port = "9092"
#    sasl_plain_username = "globex"
#    sasl_plain_password = "globex"
#    sasl_mechanism = "SCRAM-SHA-512"
#    security_protocol = "SASL_PLAINTEXT"
#    check_hostname = args.get("check_hostname", True)
#    group_id = args.get("group_id", None)
#    offset = args.get("offset", "latest")
#    encoding = args.get("encoding", "utf-8")
#    cafile = None

    topic = args.get("topic")
    host = args.get("host")
    port = args.get("port")
    sasl_plain_username = args.get("sasl_plain_username")
    sasl_plain_password = args.get("sasl_plain_password")
    sasl_mechanism = args.get("sasl_mechanism")
    security_protocol = args.get("security_protocol")
    cafile = args.get("cafile", None)
    certfile = args.get("certfile", None)
    keyfile = args.get("keyfile", None)
    password = args.get("password", None)
    check_hostname = args.get("check_hostname", True)
    group_id = args.get("group_id", None)
    offset = args.get("offset", "latest")
    encoding = args.get("encoding", "utf-8")

    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    if cafile:
        context = create_ssl_context(
            cafile=cafile,
            certfile=certfile,
            keyfile=keyfile,
            password=password,
        )
        context.check_hostname = check_hostname

    kafka_consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=f"{host}:{port}",
        group_id=group_id,
        enable_auto_commit=True,
        max_poll_records=1,
        auto_offset_reset=offset,
        security_protocol="SSL" if cafile else security_protocol,
        ssl_context=context if cafile else None,
        sasl_plain_password=sasl_plain_password,
        sasl_plain_username=sasl_plain_username,
        sasl_mechanism = None if cafile else sasl_mechanism 
    )

    await kafka_consumer.start()

    try:
        async for msg in kafka_consumer:
            data = None
            try:
                value = msg.value.decode(encoding)
                data = json.loads(value)
            except json.decoder.JSONDecodeError:
                data = value
            except UnicodeError:
                logger.exception("Unicode Error")

            if data:
                await queue.put({"body": data})
            await asyncio.sleep(0)
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self: "MockQueue", event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"},
        ),
    )
