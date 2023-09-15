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
from kafka import KafkaConsumer
import ssl

async def main(
    queue: asyncio.Queue,
    args: dict[str, Any],
) -> None:
    """Receive events via a Kafka topic."""
    logger = logging.getLogger()

#    topic = args.get("topic")
#    host = args.get("host")
#    port = args.get("port")
#    username = args.get("username")
#    password = args.get("password")
#    security_protocol = args.get("security_protocol")
#    sasl_mechanism = args.get("sasl_mechanism")

    topic = "reviews.sentiment"
    host = "kafka-kafka-bootstrap.globex-mw.svc.cluster.local"
    port = "9092"
    username = "globex"
    password = "globex"
    security_protocol = "SASL_PLAINTEXT"
    sasl_mechanism = "SCRAM-SHA-512"
    offset = "latest"

    if security_protocol not in ("SASL_PLAINTEXT", "SASL_SSL"):
        msg = f"Invalid security_protocol option: {security_protocol}"
        raise ValueError(msg)

    if sasl_mechanism not in ("PLAIN", "GSSAPI", "SCRAM-SHA-256", "SCRAM-SHA-512", "OAUTHBEARER"):
        msg = f"Invalid sasl_mechanism option: {sasl_mechanism}"
        raise ValueError(msg)

    if security_protocol == "SASL_SSL":
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")

    kafka_consumer = KafkaConsumer(
        topic,
        bootstrap_servers=f"{host}:{port}",
        sasl_plain_username=username,
        sasl_plain_password=password,
        security_protocol=security_protocol,
        sasl_mechanism=sasl_mechanism,
        ssl_context=ssl_context if security_protocol == "SASL_SSL" else None,
        auto_offset_reset="latest",  # You can change this as needed
    )

    try:
        for msg in kafka_consumer:
            data = None
            try:
                value = msg.value.decode("utf-8")  # Specify encoding if different
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
        logger.info("Stopping Kafka consumer")
        kafka_consumer.close()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self, event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {
                "topic": "reviews.sentiment",
                "host": "kafka-kafka-bootstrap.globex-mw.svc.cluster.local",
                "port": "9092",
                "sasl_mechanism": "SCRAM-SHA-512",
                "username": "globex",
                "password": "globex",
                "security_protocol": "SASL_PLAINTEXT",  # Adjust as needed
            },
        )
    )
