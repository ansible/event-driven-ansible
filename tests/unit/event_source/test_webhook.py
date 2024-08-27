import asyncio
import ssl
from http import HTTPStatus
from typing import Any

import aiohttp
import pytest

from extensions.eda.plugins.event_source.webhook import main as webhook_main


async def start_server(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    await webhook_main(queue, args)


async def post_code(server_task, info) -> None:
    url = f'http://{info["host"]}/{info["endpoint"]}'
    payload = info["payload"]

    connector = None
    if "client_certfile" in info:
        url = f'https://{info["host"]}/{info["endpoint"]}'
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.load_cert_chain(info["client_certfile"], info["client_keyfile"])
        connector = aiohttp.TCPConnector(ssl=context)
    async with aiohttp.ClientSession(connector=connector) as session:
        headers = {"Authorization": "Bearer secret"}
        async with session.post(url, json=payload, headers=headers) as resp:
            print(resp.status)

    server_task.cancel()


async def assert_post(
    server_task, info, expected_status=HTTPStatus.OK, expected_text=None
) -> None:
    url = f'http://{info["host"]}/{info["endpoint"]}'
    payload = info["payload"]
    headers = {}

    if "token" in info:
        headers["Authorization"] = f"Bearer {info['token']}"

    if "hmac_header" in info:
        headers[info["hmac_header"]] = info["hmac_digest"]

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            server_task.cancel()
            assert resp.status == expected_status
            if expected_text:
                assert expected_text in await resp.text()


async def cancel_code(server_task) -> None:
    server_task.cancel()


@pytest.mark.asyncio
async def test_cancel() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {"host": "localhost", "port": 8000, "token": "secret"}
    plugin_task = asyncio.create_task(start_server(queue, args))
    cancel_task = asyncio.create_task(cancel_code(plugin_task))

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(plugin_task, cancel_task)


@pytest.mark.asyncio
async def test_post_endpoint() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "token": "secret",
        "certfile": "./tests/unit/event_source/certs/server.crt",
        "keyfile": "./tests/unit/event_source/certs/server.key",
        "cafile": "./tests/unit/event_source/certs/client.crt",
    }
    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
        "client_certfile": "./tests/unit/event_source/certs/client.crt",
        "client_keyfile": "./tests/unit/event_source/certs/client.key",
    }

    post_task = asyncio.create_task(post_code(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]


@pytest.mark.asyncio
async def test_post_unsupported_body() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()
    args = {"host": "localhost", "port": 8000}

    async def do_request() -> None:
        async with aiohttp.ClientSession() as session:
            url = f'http://{args["host"]}:{args["port"]}/test'
            async with session.post(url, data="not a json") as resp:
                plugin_task.cancel()
                assert resp.status == HTTPStatus.BAD_REQUEST

    plugin_task = asyncio.create_task(start_server(queue, args))
    request_task = asyncio.create_task(do_request())
    await asyncio.gather(plugin_task, request_task)


@pytest.mark.asyncio
async def test_post_hmac_hex_endpoint() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-hub-signature-256",
        "hmac_format": "hex",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": args["hmac_header"],
        "hmac_digest": "sha256=9ec8272937a36a4b4427d4f9ab7b0425856c5ef5d7e1b496f864aaf99c1910ca",  # noqa: E501
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(assert_post(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]


@pytest.mark.asyncio
async def test_post_hmac_hex_wo_digest_prefix_endpoint() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-hub-signature-256",
        "hmac_format": "hex",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": args["hmac_header"],
        "hmac_digest": "9ec8272937a36a4b4427d4f9ab7b0425856c5ef5d7e1b496f864aaf99c1910ca",  # noqa: E501
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(assert_post(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]


@pytest.mark.asyncio
async def test_post_hmac_hex_endpoint_invalid_signature() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-hub-signature-256",
        "hmac_format": "hex",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": args["hmac_header"],
        "hmac_digest": "sha256=11f8feeab79372c842f0097fc105dd66d90c41412ab9d3c4071859d7b6ae864b",  # noqa: E501
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(
        assert_post(plugin_task, task_info, HTTPStatus.UNAUTHORIZED)
    )

    await asyncio.gather(plugin_task, post_task)


@pytest.mark.asyncio
async def test_post_hmac_hex_endpoint_missing_signature() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-hub-signature-256",
        "hmac_format": "hex",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": "x-not-a-signature-header",
        "hmac_digest": "sha256=205009e3e895e0fe0ff982e1020dd0fb4b6d16cf9c666652b3492e20429ccdb8",  # noqa: E501
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(
        assert_post(plugin_task, task_info, HTTPStatus.BAD_REQUEST)
    )

    await asyncio.gather(plugin_task, post_task)


@pytest.mark.asyncio
async def test_post_hmac_base64_endpoint() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-custom-signature",
        "hmac_format": "base64",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": args["hmac_header"],
        "hmac_digest": "sha256=nsgnKTejaktEJ9T5q3sEJYVsXvXX4bSW+GSq+ZwZEMo=",
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(assert_post(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]


@pytest.mark.asyncio
async def test_post_hmac_base64_endpoint_invalid_signature() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "hmac_secret": "secret",
        "hmac_algo": "sha256",
        "hmac_header": "x-hub-signature-256",
        "hmac_format": "hex",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": args["hmac_header"],
        "hmac_digest": "nsgnKTejaktEJ9T5q3sEJYVsXvXX4bSW+GSq+ZwZEMo=",
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(
        assert_post(plugin_task, task_info, HTTPStatus.UNAUTHORIZED)
    )

    await asyncio.gather(plugin_task, post_task)


@pytest.mark.asyncio
async def test_post_token_and_hmac_hex_endpoint() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "token": "secret",
        "hmac_secret": "secret",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": "x-hub-signature-256",
        "hmac_digest": "sha256=9ec8272937a36a4b4427d4f9ab7b0425856c5ef5d7e1b496f864aaf99c1910ca",  # noqa: E501
        "token": args["token"],
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    post_task = asyncio.create_task(assert_post(plugin_task, task_info))

    await asyncio.gather(plugin_task, post_task)

    data = await queue.get()
    assert data["payload"] == task_info["payload"]
    assert data["meta"]["endpoint"] == task_info["endpoint"]
    assert data["meta"]["headers"]["Host"] == task_info["host"]


@pytest.mark.asyncio
async def test_post_token_and_hmac_hex_endpoint_invalid_signature() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = args = {
        "host": "localhost",
        "port": 8000,
        "token": "secret",
        "hmac_secret": "secret",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": "x-hub-signature-256",
        "hmac_digest": "11f8feeab79372c842f0097fc105dd66d90c41412ab9d3c4071859d7b6ae864b",  # noqa: E501
        "token": args["token"],
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    expected_text = "HMAC verification failed"
    post_task = asyncio.create_task(
        assert_post(plugin_task, task_info, HTTPStatus.UNAUTHORIZED, expected_text)
    )

    await asyncio.gather(plugin_task, post_task)


@pytest.mark.asyncio
async def test_post_token_and_hmac_hex_endpoint_invalid_token() -> None:
    queue: asyncio.Queue[Any] = asyncio.Queue()

    args = {
        "host": "localhost",
        "port": 8000,
        "token": "secret",
        "hmac_secret": "secret",
    }

    plugin_task = asyncio.create_task(start_server(queue, args))

    task_info = {
        "payload": {"src_path": "https://example.com/payload"},
        "hmac_header": "x-hub-signature-256",
        "hmac_digest": "11f8feeab79372c842f0097fc105dd66d90c41412ab9d3c4071859d7b6ae864b",  # noqa: E501
        "token": "invalid_token",
        "endpoint": "test",
        "host": f'{args["host"]}:{args["port"]}',
    }

    expected_text = "Invalid authorization token"
    post_task = asyncio.create_task(
        assert_post(plugin_task, task_info, HTTPStatus.UNAUTHORIZED, expected_text)
    )

    await asyncio.gather(plugin_task, post_task)
