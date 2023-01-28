"""
nats.py

An ansible-rulebook event source plugin for receiving events via a NATS Jestream.

Arguments:
    host:      The host where the stream is hosted can contain the full url with port
    username:  The optional username to be used
    password:  The optional password to be used
    token:     The optional token to be used

    stream:         The stream name
    subject:        The subject name
    durable:        The name of the durable consumer
    queue:          The queue name of subscription for distributing requests
    deliver_policy: The Policy for deliver msg on start can be all|last|new, default all

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
    stream = args.get("stream")
    subject = args.get("subject")
    durable = args.get("durable")
    nats_queue = args.get("queue")
    deliver_policy = args.get("deliver_policy", "all")

    # Check params
    if username and token:
        logger.error("username and token can't be set together")
        raise Exception("username and token can't be set together")

    if deliver_policy not in ["all", "last", "new"]:
        logger.error(f"deliver_policy must be one of all|last|new not {deliver_policy}")
        raise Exception(f"deliver_policy must be one of all|last|new not {deliver_policy}")

    # Initialise connection
    nc = await nats.connect(servers=host,
                            user=username,
                            password=password,
                            token=token)
    js = nc.jetstream()
    logger.info("Successfully connected to NATS Jetstream")

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
            await msg.ack()
        except json.decoder.JSONDecodeError as e:
            logger.error(e)

    # Subscribe to stream
    sub = await js.subscribe(subject=subject,
                            stream=stream,
                            durable=durable,
                            cb=msg_handler,
                            deliver_policy=deliver_policy,
                            queue=nats_queue)
    logger.info("Successfully subscribed to stream")

    # Wait messages from NATS js
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"stream": "eda", "subject": "mock",
                                    "host": "nats://localhost:4222"}))
