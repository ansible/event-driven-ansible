"""
azure_service_bus.py

An ansible-rulebook event source module for receiving events from an Azure service bus

Arguments:
    conn_str: The connection string to connect to the Azure service bus
    queue_name: The name of the queue to pull messages from
    logging_enable: Whether to turn on logging. Default to True

Example:

    - ansible.eda.azure_service_bus:
        conn_str: "{{connection_str}}"
        queue_name: "{{queue_name}}"

"""

import asyncio
import concurrent.futures
import json
from typing import Any, Dict

from azure.servicebus import ServiceBusClient


def receive_events(
    loop: asyncio.events.AbstractEventLoop, queue: asyncio.Queue, args: Dict[str, Any]
):
    servicebus_client = ServiceBusClient.from_connection_string(
        conn_str=args["conn_str"], logging_enable=bool(args.get("logging_enable", True))
    )

    with servicebus_client:
        receiver = servicebus_client.get_queue_receiver(queue_name=args["queue_name"])
        with receiver:
            for msg in receiver:
                meta = {"message_id": msg.message_id}
                body = str(msg)
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    pass
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"body": body, "meta": meta}
                )
                receiver.complete_message(msg)


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    loop = asyncio.get_running_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as task_pool:
        await loop.run_in_executor(task_pool, receive_events, loop, queue, args)


if __name__ == "__main__":

    class MockQueue:
        def put_nowait(self, event):
            print(event)

    args = {
        "conn_str": "Endpoint=sb://foo.servicebus.windows.net/",
        "queue_name": "eda-queue",
    }
    asyncio.run(main(MockQueue(), args))
