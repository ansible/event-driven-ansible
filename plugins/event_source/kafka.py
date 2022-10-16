"""
kafka.py

An ansible-rulebook event source plugin for receiving events via a kafka topic.

Arguments:
    host:      The host where the kafka topic is hosted
    port:      The port where the kafka server is listening
    topic:     The kafka topic
    group_id:  A kafka group id
    offset:    Where to automatically reset the offset. [latest, earliest]
               Default to latest



"""

import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from typing import Any, Dict


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    logger = logging.getLogger()

    topic = args.get("topic")
    host = args.get("host")
    port = args.get("port")
    group_id = args.get("group_id", None)
    offset = args.get("offset", "latest")

    if offset not in ("latest", "earliest"):
        raise Exception(f"Invalid offset option: {offset}")

    kafka_consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers="{0}:{1}".format(host, port),
        group_id=group_id,
        enable_auto_commit=True,
        max_poll_records=1,
        auto_offset_reset=offset,
    )
    await kafka_consumer.start()

    try:
        async for msg in kafka_consumer:
            try:
                data = json.loads(msg.value)
                await queue.put(data)
            except json.decoder.JSONDecodeError as e:
                logger.error(e)
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()

if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"}))
