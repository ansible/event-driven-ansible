import asyncio
from typing import Any, Optional, Type
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
    def __init__(self, payloads: list[Any]) -> None:
        self.payloads = payloads
        self._idx = 0

    async def __aenter__(self) -> "AsyncReceiver":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Any,
    ) -> None:
        pass

    def __aiter__(self) -> "AsyncReceiver":
        return self

    async def __anext__(self) -> Any:
        if self._idx < len(self.payloads):
            val = self.payloads[self._idx]
            self._idx += 1
            return val
        raise StopAsyncIteration

    async def complete_message(self, msg: Any) -> None:
        pass


class AsyncServiceBusClient:
    def __init__(self, receiver: AsyncReceiver) -> None:
        self.receiver = receiver

    async def __aenter__(self) -> "AsyncServiceBusClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Any,
    ) -> None:
        pass

    def get_queue_receiver(self, queue_name: Optional[str] = None) -> AsyncReceiver:
        return self.receiver


@pytest.mark.asyncio
async def test_receive_from_azure_service_bus(myqueue: MockQueue) -> None:
    payload1 = MagicMock()
    payload1.message_id = 1
    payload1.__str__ = lambda self=payload1: "Hello World"  # type: ignore[assignment]

    payload2 = MagicMock()
    payload2.message_id = 2
    payload2.__str__ = lambda self=payload2: '{"Say":"Hello World"}'  # type: ignore[assignment]

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
