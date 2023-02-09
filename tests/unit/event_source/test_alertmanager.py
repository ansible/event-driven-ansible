import asyncio

import aiohttp
import pytest

from plugins.event_source.alertmanager import main as alert_main


async def start_server(queue, args):
    await alert_main(queue, args)


async def post_code(server_task, info):
    url = f'http://{info["host"]}/{info["endpoint"]}'
    payload = info["payload"]

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            print(resp.status)

    server_task.cancel()


async def cancel_code(server_task):
    server_task.cancel()


@pytest.mark.asyncio
async def test_cancel():
    queue = asyncio.Queue()

    args = {"host": "127.0.0.1", "port": 8000}
    plugin_task = asyncio.create_task(start_server(queue, args))
    cancel_task = asyncio.create_task(cancel_code(plugin_task))

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(plugin_task, cancel_task)


@pytest.mark.asyncio
async def test_post_endpoint_with_default():
    queue = asyncio.Queue()

    args = {"host": "127.0.0.1", "port": 8000}
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
    assert data["alert"] == task_info["payload"]["alerts"][0]
    assert data["meta"]["hosts"] == ["host1"]

    data = await queue.get()
    assert data["alert"] == task_info["payload"]["alerts"][1]
    assert data["meta"]["hosts"] == ["host2"]

    assert queue.empty()


@pytest.mark.asyncio
async def test_post_endpoint_with_options():
    queue = asyncio.Queue()

    args = {
        "host": "127.0.0.1",
        "port": 8000,
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
