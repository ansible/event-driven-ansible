import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from extensions.eda.plugins.event_source.azure_service_bus import main as azure_main


class MockQueue(asyncio.Queue[Any]):
    def __init__(self) -> None:
        self.queue: list[Any] = []

    def put_nowait(self, item: Any) -> None:
        self.queue.append(item)


@pytest.fixture
def myqueue() -> MockQueue:
    return MockQueue()


def test_receive_from_azure_service_bus(myqueue: MockQueue) -> None:
    client = MagicMock()
    with patch(
        "extensions.eda.plugins.event_source.azure_service_bus.ServiceBusClient."
        "from_connection_string",
        return_value=client,
    ):
        payload1 = MagicMock()
        payload1.message_id = 1
        payload1.__str__.return_value = "Hello World"  # type: ignore[attr-defined]

        payload2 = MagicMock()
        payload2.message_id = 2
        payload2.__str__.return_value = '{"Say":"Hello World"}'  # type: ignore[attr-defined]

        receiver = MagicMock()
        receiver.__iter__.return_value = [payload1, payload2]
        client.get_queue_receiver.return_value = receiver
        asyncio.run(
            azure_main(
                myqueue,
                {
                    "conn_str": "Endpoint=sb://foo.servicebus.windows.net/",
                    "queue_name": "eda-queue",
                },
            )
        )
        assert myqueue.queue[0] == {"body": "Hello World", "meta": {"message_id": 1}}
        assert myqueue.queue[1] == {
            "body": {"Say": "Hello World"},
            "meta": {"message_id": 2},
        }
        assert len(myqueue.queue) == 2
