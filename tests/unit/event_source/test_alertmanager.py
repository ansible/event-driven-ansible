import asyncio
import contextlib
from typing import Any

import aiohttp
import pytest
from multidict import CIMultiDict, CIMultiDictProxy

from extensions.eda.plugins.event_source.alertmanager import (
    _event_headers,
)
from extensions.eda.plugins.event_source.alertmanager import main as alert_main


async def start_server(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
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


async def _post_with_auth(
    args: dict[str, Any], headers: dict[str, str]
) -> tuple[int, asyncio.Queue[Any]]:
    queue: asyncio.Queue[Any] = asyncio.Queue()
    plugin_task = asyncio.create_task(start_server(queue, args))
    await asyncio.sleep(0.1)

    url = f'http://{args["host"]}:{args["port"]}/test'
    payload = {"alerts": [{"labels": {"instance": "host1"}}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            status = resp.status

    plugin_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await plugin_task
    return status, queue


@pytest.mark.asyncio
async def test_post_with_valid_token() -> None:
    args = {"host": "localhost", "port": 8004, "token": "secret"}
    status, queue = await _post_with_auth(args, {"Authorization": "Bearer secret"})

    assert status == 202
    data = await queue.get()
    assert "Authorization" not in data["meta"]["headers"]
    data = await queue.get()
    assert "Authorization" not in data["meta"]["headers"]
    assert data["meta"]["hosts"] == ["host1"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("port", "headers"),
    [
        (8005, {}),
        (8006, {"Authorization": "Bearer wrong"}),
        (8007, {"Authorization": "Basic secret"}),
        (8008, {"Authorization": "Bearer"}),
    ],
)
async def test_post_with_invalid_token(port: int, headers: dict[str, str]) -> None:
    args = {"host": "localhost", "port": port, "token": "secret"}
    status, queue = await _post_with_auth(args, headers)

    assert status == 401
    assert queue.empty()


@pytest.mark.asyncio
async def test_status_does_not_require_token() -> None:
    args = {"host": "localhost", "port": 8009, "token": "secret"}
    queue: asyncio.Queue[Any] = asyncio.Queue()
    plugin_task = asyncio.create_task(start_server(queue, args))
    await asyncio.sleep(0.1)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:{args['port']}/") as resp:
            status = resp.status

    plugin_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await plugin_task
    assert status == 200


@pytest.mark.parametrize("name", ["Authorization", "authorization", "AUTHORIZATION"])
def test_event_headers_drops_authorization_in_any_case(name: str) -> None:
    raw = CIMultiDictProxy(CIMultiDict([(name, "Bearer secret"), ("Host", "h")]))

    assert _event_headers(raw) == {"Host": "h"}
