"""
rabbitmq.py
An ansible-rulebook event source plugin for receiving events via RabbitMQ

author:
    - Timothy Test (@ttestscripting)

Arguments:
    host       The RabbitMQ host
    port       The port for RabbitMQ
               Default 5672
    v_host:    Virtual Host
               Default '/'
    username:  The RabbitMQ username
               Default guest
    password:  The RabbitMQ password
               Default guest
    queue:     queue to watch
"""

import asyncio
import logging
import aio_pika
from typing import Any, Dict

async def main(queue: asyncio.Queue, args: Dict[str, Any]):

    logger = logging.getLogger()

    rabbitmq_host = args.get("host")
    rabbitmq_port = args.get("port", "5672")
    rabbitmq_v_host = args.get("v_host", "/")
    rabbitmq_username = args.get("username", "guest")
    rabbitmq_password = args.get("password", "guest")
    rabbitmq_queue = args.get("queue")
    # TODO add options for SSL
    connection = await aio_pika.connect_robust(
        host=rabbitmq_host,
        login=rabbitmq_username,
        password=rabbitmq_password,
        port=rabbitmq_port,
        virtualhost=rabbitmq_v_host
    )

    async with connection:

        # Creating channel
        channel: aio_pika.abc.AbstractChannel = await connection.channel()

        # Declaring queue
        mq_queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(rabbitmq_queue)

        async with mq_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info(message.body.decode())
                    data = dict(
                           message_body=message.body.decode(),
                           meta=dict(host=rabbitmq_host,
                                     queue=rabbitmq_queue,
                                     v_host=rabbitmq_v_host,
                                     message_info=message.info()),
                          )
                    await queue.put(data)
                    logger.info(data)
                    if mq_queue.name in message.body.decode():
                        break

if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"host": "localhost", "port": "5672", "queue": "test"}))