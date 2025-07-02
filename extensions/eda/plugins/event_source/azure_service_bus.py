import asyncio
import contextlib
import json
from typing import Any

from azure.servicebus.aio import ServiceBusClient

DOCUMENTATION = r"""
---
short_description: Receive events from an Azure service bus.
description:
  - An ansible-rulebook event source module for receiving events from an Azure service bus.
  - In order to get the service bus and the connection string, refer to
    https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-python-how-to-use-queues?tabs=passwordless
options:
  conn_str:
    description:
      - The connection string to connect to the Azure service bus.
    type: str
    required: true
  queue_name:
    description:
      - The name of the queue to pull messages from.
    type: str
    required: true
  logging_enable:
    description:
      - Whether to turn on logging.
    type: bool
    default: true
"""

EXAMPLES = r"""
- ansible.eda.azure_service_bus:
    conn_str: "{{connection_str}}"
    queue_name: "{{queue_name}}"
"""


async def receive_events(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],  # pylint: disable=W0621
) -> None:
    """Receive events from service bus asynchronously."""
    servicebus_client = ServiceBusClient.from_connection_string(
        conn_str=args["conn_str"],
        logging_enable=bool(args.get("logging_enable", True)),
    )

    async with servicebus_client:
        receiver = servicebus_client.get_queue_receiver(queue_name=args["queue_name"])
        async with receiver:
            async for msg in receiver:
                meta = {"message_id": msg.message_id}
                body = str(msg)
                with contextlib.suppress(json.JSONDecodeError):
                    body = json.loads(body)

                await queue.put({"body": body, "meta": meta})
                await receiver.complete_message(msg)


async def main(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],  # pylint: disable=W0621
) -> None:
    """Receive events from service bus in a loop."""
    await receive_events(queue, args)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    args = {
        "conn_str": "Endpoint=sb://foo.servicebus.windows.net/",
        "queue_name": "eda-queue",
    }
    asyncio.run(main(MockQueue(), args))
