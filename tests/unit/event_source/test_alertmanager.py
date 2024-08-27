import asyncio
from typing import Any

import aiohttp
import pytest

from extensions.eda.plugins.event_source.alertmanager import main as alert_main


async def start_server(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    await alert_main(queue, args)


async def post_code(server_task: asyncio.Task[None], info: dict[str, Any]) -> None:
    url = f'http://{info["host"]}/{info["endpoint"]}'
    payload = info["payload"]

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            print(resp.status)

    server_task.cancel()


async def cancel_code(server_task: asyncio.Task[None]) -> None:
    server_task.cancel()


@pytest.mark.asyncio
async def test_cancel() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {"host": "localhost", "port": 8001}
    plugin_task = asyncio.create_task(start_server(queue, args))
    cancel_task = asyncio.create_task(cancel_code(plugin_task))

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(plugin_task, cancel_task)


@pytest.mark.asyncio
async def test_post_endpoint_with_default() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {"host": "localhost", "port": 8002}
    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {
            "alerts": [
                {
                    "message": "abc",
                    "labels": {"instance": "host1"},
                },
                {
                    "message": "xyz",
                    "labels": {"instance": "host2"},
                },
            ]
        },
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(post_code(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]

    data = await queue.get()
    assert isinstance(data, dict)
    assert isinstance(task_info["payload"], dict)
    assert isinstance(task_info["payload"]["alerts"], list)
    assert data["alert"] == task_info["payload"]["alerts"][0]
    assert data["meta"]["hosts"] == ["host1"]

    data = await queue.get()
    assert isinstance(data, dict)
    assert data["alert"] == task_info["payload"]["alerts"][1]
    assert data["meta"]["hosts"] == ["host2"]

    assert queue.empty()


@pytest.mark.asyncio
async def test_post_endpoint_with_options() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8003,
        "data_alerts_path": "",
        "data_host_path": "node",
        "skip_original_data": True,
    }
    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"message": "abc", "node": "host1"},
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(post_code(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["alert"] == task_info["payload"]
    assert data["meta"]["hosts"] == ["host1"]

    assert queue.empty()
