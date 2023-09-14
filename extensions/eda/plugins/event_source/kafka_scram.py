"""kafka_scram.py.

An ansible-rulebook event source plugin for receiving events via a kafka topic authentication using SCRAM-SHA-512..

Arguments:
---------
    host:      The host where the kafka topic is hosted
    port:      The port where the kafka server is listening
    security_protocol: Set Security protocol. See details in next point below.
    sasl_mechanism (str): Authentication mechanism when security_protocol
        is configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid values are:
        ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,
        ``OAUTHBEARER``.
        Default: ``PLAIN``
    username (str): username for SASL ``PLAIN`` authentication.
        Default: None
    password (str): password for SASL ``PLAIN`` authentication.
        Default: None
    topic:     The kafka topic
    offset:    Where to automatically reset the offset. [latest, earliest]
               Default to latest

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

    topic = args.get("topic")
    host = args.get("host")
    port = args.get("port")
    username  = args.get("username")
    password = args.get("password")
    security_protocol = args.get("security_protocol")
    sasl_mechanism = args.get("sasl_mechanism")
    offset = args.get("offset", "latest")    

# EXAMPLE
#    topic = "reviews.sentiment"
#    host = "kafka-kafka-bootstrap.globex-mw.svc.cluster.local"
#    port = "9092"
#    username  = "globex"
#    password = "globex"
#    security_protocol = "SASL_PLAINTEXT"
#    sasl_mechanism = "SCRAM-SHA-512"

    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    kafka_consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=f"{host}:{port}",
        sasl_plain_username=username,
        sasl_plain_password=password,
        security_protocol=security_protocol,
        sasl_mechanism=sasl_mechanism,
        auto_offset_reset=offset,      
    )

    await kafka_consumer.start()

    try:
        async for msg in kafka_consumer:
            data = None
            try:
                value = msg.value.decode(encoding)
                print(value)
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
