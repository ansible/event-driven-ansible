"""
nats.py

An ansible-rulebook event source plugin for receiving events via a NATS.

Arguments:
    host:      The host where the stream is hosted can contain the full url with port
    username:  The optional username to be used
    password:  The optional password to be used
    token:     The optional token to be used

    subject:        The subject name
    queue:          The group name of subscription for distributing requests

"""

import asyncio
import json
import logging
from typing import Any, Dict
import nats


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    # connection params
    host = args.get("host")
    username = args.get("username")
    password = args.get("password")
    token = args.get("token")

    # Stream Subscription params
    subject = args.get("subject")
    nats_queue = args.get("queue")

    # Check params
    if username and token:
        logger.error("username and token can't be set together")
        raise Exception("username and token can't be set together")

    # Initialise connection
    nc = await nats.connect(servers=host,
                            user=username,
                            password=password,
                            token=token)
    logger.info("Successfully connected to NATS server")

    # Handler for receiver nats msg
    async def msg_handler(msg):

        try:
            msg_reply = msg.reply
            msg_subject = msg.subject
            msg_headers = msg.headers
            data = json.loads(msg.data.decode())
            await queue.put({"payload": data,
                            "meta": {"reply": msg_reply,
                                    "subject": msg_subject,
                                    "headers": msg_headers}
                            })
        except json.decoder.JSONDecodeError as e:
            logger.error(e)

    # Subscribe to stream
    sub = await nc.subscribe(subject=subject,
                            cb=msg_handler,
                            queue=nats_queue)
    logger.info("Successfully subscribed to subject NATS")

    # Wait messages from NATS js
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"subject": "mock", "host": "nats://localhost:4222"}))
