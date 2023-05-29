import asyncio

import aiohttp
import pytest

from extensions.eda.plugins.event_source.webhook import main as webhook_main


async def start_server(queue, args):
    await webhook_main(queue, args)


async def post_code(server_task, info):
    url = f'http://{info["host"]}/{info["endpoint"]}'
    payload = info["payload"]

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": "Bearer secret"}
        async with session.post(url, json=payload, headers=headers) as resp:
            print(resp.status)

    server_task.cancel()


async def cancel_code(server_task):
    server_task.cancel()


@pytest.mark.asyncio
async def test_cancel():
    queue = asyncio.Queue()

    args = {"host": "127.0.0.1", "port": 8000, "token": "secret"}
    plugin_task = asyncio.create_task(start_server(queue, args))
    cancel_task = asyncio.create_task(cancel_code(plugin_task))

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(plugin_task, cancel_task)


@pytest.mark.asyncio
async def test_post_endpoint():
    queue = asyncio.Queue()

    args = {"host": "127.0.0.1", "port": 8000, "token": "secret"}
    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(post_code(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]
