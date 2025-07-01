import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from extensions.eda.plugins.event_source.azure_service_bus import main as azure_main


class MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    async def put(self, item: Any) -> None:
        self.queue.append(item)


@pytest.fixture
def myqueue() -> MockQueue:
    return MockQueue()


class AsyncReceiver:
    def __init__(self, payloads):
        self.payloads = payloads
        self._idx = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx < len(self.payloads):
            val = self.payloads[self._idx]
            self._idx += 1
            return val
        raise StopAsyncIteration

    async def complete_message(self, msg):
        pass


class AsyncServiceBusClient:
    def __init__(self, receiver):
        self.receiver = receiver

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get_queue_receiver(self, queue_name=None):
        return self.receiver


@pytest.mark.asyncio
async def test_receive_from_azure_service_bus(myqueue: MockQueue) -> None:
    payload1 = MagicMock()
    payload1.message_id = 1
    payload1.__str__.return_value = "Hello World"

    payload2 = MagicMock()
    payload2.message_id = 2
    payload2.__str__.return_value = '{"Say":"Hello World"}'

    receiver = AsyncReceiver([payload1, payload2])
    client = AsyncServiceBusClient(receiver)

    with patch(
        "extensions.eda.plugins.event_source.azure_service_bus.ServiceBusClient.from_connection_string",
        return_value=client,
    ):
        await azure_main(
            myqueue,
            {
                "conn_str": "Endpoint=sb://foo.servicebus.windows.net/",
                "queue_name": "eda-queue",
            },
        )
        assert myqueue.queue[0] == {"body": "Hello World", "meta": {"message_id": 1}}
        assert myqueue.queue[1] == {
            "body": {"Say": "Hello World"},
            "meta": {"message_id": 2},
        }
        assert len(myqueue.queue) == 2
