"""mqtt.py.

An ansible-rulebook event source plugin for receiving events via a mqtt topic.

Arguments:
---------
    host:               The host where the mqtt topic is hosted
    port:               The port where the mqtt server is listening
    username:           The username to connect to the broker
    password:           The password to connect to the broker
    ca_certs            The optional certificate authority file path containing
                        certificate used to sign mqtt broker certificates
    validate_certs      Disable certificate validation - true/false
    certfile            The optional client certificate file path containing
                        the client certificate, as well as CA certificates needed
                        to establish the certificate's authenticity
    keyfile             The optional client key file path containing the client
                        private key
    keyfile_password    The optional password to be used when loading the
                        certificate chain
    topic:              The mqtt topic to subscribe to

"""

import asyncio
import json
import logging
from typing import Any

import aiomqtt as aiomqtt


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Receive events via a MQTT topic."""
    logger = logging.getLogger()

    topic = args.get("topic")

    host = args.get("host")
    port = int(args.get("port"))
    username = args.get("username")
    password = args.get("password")

    ca_certs = args.get("ca_certs")
    validate_certs = bool(args.get("validate_certs"))
    certfile = args.get("certfile")
    keyfile = args.get("keyfile")
    keyfile_password = args.get("keyfile_password")

    if ca_certs:
        tls_params = aiomqtt.TLSParameters(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
            keyfile_password=keyfile_password,
            cert_reqs=validate_certs if validate_certs is not None else True,
        )

    mqtt_consumer = aiomqtt.Client(
        hostname=host,
        port=port,
        username=username,
        password=password,
        tls_params=tls_params if ca_certs else None,
    )

    await mqtt_consumer.connect()

    try:
        async with mqtt_consumer.messages() as messages:
            await mqtt_consumer.subscribe(topic)
            async for message in messages:
                try:
                    data = json.loads(message.payload.decode())
                    await queue.put(data)
                except json.decoder.JSONDecodeError:
                    logger.exception("Decoding exception for incoming message")
    finally:
        logger.info("Disconneccting from broker")
        mqtt_consumer.disconnect()


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
            {"topic": "eda", "host": "localhost", "port": "1883"},
        ),
    )
