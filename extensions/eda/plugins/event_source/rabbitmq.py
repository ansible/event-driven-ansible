"""rabbitmq.py

An ansible-rulebook event source plugin for receiving events via a RabbitMQ queue.

Arguments:
---------
    host:      The host where rabbitmq is hosted
    port:      The port where the rabbitmq server is listening

"""

import asyncio
import json
import logging
from typing import Any


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Receive events via a rabbitmq topic."""
    logger = logging.getLogger()
