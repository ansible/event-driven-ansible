"""
rabbitmq.py
An ansible-rulebook event source plugin for receiving events via RabbitMQ
Arguments:
    host:           The RabbitMQ host
    port:           The port for RabbitMQ
                    Default 5672
    v_host:         Virtual Host
                    Default '/'
    username:       The RabbitMQ username
                    Default guest
    password:       The RabbitMQ password
                    Default guest
    cafile:         The optional certificate authority file path containing
                    certificates used to sign rabbitmq certificates
    certfile:       The optional client certificate file path containing
                    the client certificate, as well as CA certificates
                    needed to establish the certificate's authenticity
    keyfile:        The optional client key file path containing the client
                    private key
    certpassword:   The optional password to be used when loading the
                    certificate chain
    check_hostname: Enable SSL hostname verification. [True (default), False]
    queue:          queue to watch
"""

import asyncio
import json
import logging
import ssl
from typing import Any, Dict

import aio_pika


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    rabbitmq_host = args.get("host")
    rabbitmq_port = args.get("port", "5672")
    rabbitmq_v_host = args.get("v_host", "/")
    rabbitmq_username = args.get("username", "guest")
    rabbitmq_password = args.get("password", "guest")
    rabbitmq_queue = args.get("queue")
    rabbitmq_cafile = args.get("cafile")
    rabbitmq_cert = args.get("certfile")
    rabbitmq_keyfile = args.get("keyfile")
    rabbitmq_certpass = args.get("certpassword")
    rabbitmq_check_hostname = args.get("check_hostname", True)

    if rabbitmq_cafile:
        ssl_context = ssl.create_default_context(cafile=rabbitmq_cafile)
        ssl_context.load_cert_chain(
            rabbitmq_cert, keyfile=rabbitmq_keyfile, password=rabbitmq_certpass
        )
        ssl_context.check_hostname = rabbitmq_check_hostname

    connection = await aio_pika.connect_robust(
        host=rabbitmq_host,
        login=rabbitmq_username,
        password=rabbitmq_password,
        port=rabbitmq_port,
        virtualhost=rabbitmq_v_host,
        ssl=True if rabbitmq_cafile else False,
        ssl_context=ssl_context if rabbitmq_cafile else None,
    )

    async with connection:
        # Creating channel
        channel: aio_pika.abc.AbstractChannel = await connection.channel()

        # Declaring queue
        mq_queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            rabbitmq_queue
        )

        async with mq_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        await queue.put(data)
                    except json.decoder.JSONDecodeError as e:
                        logger.error(e)
                    if mq_queue.name in message.body.decode():
                        break


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(
        main(
            MockQueue(),
            {"host": "localhost", "port": "5672", "queue": "test"},
        )
    )
