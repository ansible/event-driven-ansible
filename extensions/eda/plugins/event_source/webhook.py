from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import ssl
import typing
from typing import Any

from aiohttp import web

DOCUMENTATION = r"""
---
short_description: Receive events via a webhook.
description:
  - An ansible-rulebook event source module for receiving events via a webhook.
    The message must be a valid JSON object.
  - The body received from the webhook post is placed under the key payload in
    the data pushed to the event queue. Do not expect the host(s) in the path,
    "payload.meta.limit" will be automatically used to limit an ansible action
    running on these hosts. Use insert_hosts_to_meta filter instead. See
    https://ansible.readthedocs.io/projects/rulebook/en/latest/host_limit.html
    for more details.
options:
  host:
    description:
      - The hostname to listen to.
    type: str
    default: "0.0.0.0"
  port:
    description:
      - The TCP port to listen to..
    type: str
    required: true
  token:
    description:
      - The optional authentication token expected from client.
    type: str
  certfile:
    description:
      - The optional path to a certificate file to enable TLS support.
    type: str
  keyfile:
    description:
      - The optional path to a key file to be used together with certfile.
    type: str
  password:
    description:
      - The optional password to be used when loading the certificate chain.
    type: str
  cafile:
    description:
      - The optional path to a file containing CA certificates used to validate clients' certificates.
    type: str
  capath:
    description:
      - The optional path to a directory containing CA certificates.
      - Provide either cafile or capath to enable mTLS support.
    type: str
  hmac_secret:
    description:
      - The optional HMAC secret used to verify the payload from the client.
    type: str
  hmac_algo:
    description:
      - The optional HMAC algorithm used to calculate the payload hash.
      - See your python's hashlib.algorithms_available set for available options.
    type: str
    default: "sha256"
  hmac_header:
    description:
      - The optional HMAC header sent by the client with the payload signature.
    type: str
    default: "x-hub-signature-256"
  hmac_format:
    description:
      - The optional HMAC signature format format.
    type: str
    default: "hex"
    choices: ["hex", "base64"]
"""

EXAMPLES = r"""
- ansible.eda.webhook:
    port: 6666
    host: 0.0.0.0
    hmac_secret: "secret"
    hmac_algo: "sha256"
    hmac_header: "x-hub-signature-256"
    hmac_format: "base64"
"""

if typing.TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.post(r"/{endpoint:.*}")
async def webhook(request: web.Request) -> web.Response:
    """Return response to webhook request."""
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        logger.warning("Wrong body request: failed to decode JSON payload: %s", exc)
        raise web.HTTPBadRequest(text="Invalid JSON payload") from None
    endpoint = request.match_info["endpoint"]
    headers = dict(request.headers)
    headers.pop("Authorization", None)
    data = {
        "payload": payload,
        "meta": {"endpoint": endpoint, "headers": headers},
    }
    await request.app["queue"].put(data)
    return web.Response(text=endpoint)


def _parse_token(request: web.Request) -> tuple[str, str]:
    scheme, token = request.headers["Authorization"].strip().split(" ")
    if scheme != "Bearer":
        raise web.HTTPUnauthorized(text="Only Bearer type is accepted")
    if token != request.app["token"]:
        raise web.HTTPUnauthorized(text="Invalid authorization token")
    return scheme, token


async def _hmac_verify(request: web.Request) -> bool:
    hmac_secret = request.app["hmac_secret"]
    hmac_header = request.app["hmac_header"]
    hmac_algo = request.app["hmac_algo"]
    hmac_format = request.app["hmac_format"]

    if hmac_header not in request.headers:
        raise web.HTTPBadRequest(text="Signature header not found")

    hmac_header_digest = request.headers[hmac_header].strip()

    if hmac_header_digest.startswith(f"{hmac_algo}="):
        hmac_prefix_len = len(f"{hmac_algo}=")
        hmac_header_digest = hmac_header_digest[hmac_prefix_len:]

    body = await request.text()

    event_hmac = hmac.new(
        key=hmac_secret,
        msg=body.encode("utf-8"),
        digestmod=hmac_algo,
    )
    if hmac_format == "base64":
        event_digest = base64.b64encode(event_hmac.digest()).decode("utf-8")
    elif hmac_format == "hex":
        event_digest = event_hmac.hexdigest()
    else:
        msg = f"Unsupported HMAC header format {hmac_format}"
        raise ValueError(msg)

    return hmac.compare_digest(hmac_header_digest, event_digest)


@web.middleware
async def bearer_auth(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """Verify authorization is Bearer type."""
    try:
        _parse_token(request)
    except KeyError:
        raise web.HTTPUnauthorized(reason="Missing authorization token") from None
    except ValueError:
        raise web.HTTPUnauthorized(text="Invalid authorization token") from None

    return await handler(request)


@web.middleware
async def hmac_verify(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """Verify event's HMAC signature."""
    hmac_verified = await _hmac_verify(request)
    if not hmac_verified:
        raise web.HTTPUnauthorized(text="HMAC verification failed")

    return await handler(request)


def _get_ssl_context(args: dict[str, Any]) -> ssl.SSLContext | None:
    context = None
    if "certfile" in args:
        certfile = args.get("certfile")
        keyfile = args.get("keyfile")
        password = args.get("password")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        if not isinstance(certfile, str):  # pragma: no-cover
            msg = f"certfile is not a string, got a {type(certfile)} instead."
            raise TypeError(msg)
        try:
            context.load_cert_chain(certfile, keyfile, password)
        except Exception:
            logger.exception("Failed to load certificates. Check they are valid")
            raise
        cafile = args.get("cafile")
        capath = args.get("capath")
        if cafile or capath:
            try:
                context.load_verify_locations(cafile, capath)
            except Exception:
                logger.exception("Failed to load CA certificates. Check they are valid")
                raise
            context.verify_mode = ssl.CERT_REQUIRED
    return context


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via webhook."""
    if "port" not in args:
        msg = "Missing required argument: port"
        raise ValueError(msg)

    middlewares = []
    app_attrs = {}

    if "token" in args:
        middlewares.append(bearer_auth)
        app_attrs["token"] = args["token"]

    if "hmac_secret" in args:
        middlewares.append(hmac_verify)

        app_attrs["hmac_secret"] = args["hmac_secret"].encode("utf-8")
        app_attrs["hmac_algo"] = args.get("hmac_algo", "sha256")
        if app_attrs["hmac_algo"] not in hashlib.algorithms_available:
            msg = f"Unsupported HMAC algorithm: {app_attrs['hmac_algo']}"
            raise ValueError(msg)
        app_attrs["hmac_header"] = args.get("hmac_header", "x-hub-signature-256")
        app_attrs["hmac_format"] = args.get("hmac_format", "hex")
        if app_attrs["hmac_format"] not in ["hex", "base64"]:
            msg = f"Unsupported HMAC header format {app_attrs['hmac_format']}"
            raise ValueError(msg)

    app = web.Application(middlewares=middlewares)
    for key, value in app_attrs.items():
        app[key] = value
    app["queue"] = queue

    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        args.get("host") or "0.0.0.0",  # noqa: S104
        args.get("port"),
        ssl_context=_get_ssl_context(args),
    )
    await site.start()

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Webhook Plugin Task Cancelled")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: MockQueue, event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {
                "port": 2345,
                "token": "hello",
                "certfile": "cert.pem",
                "keyfile": "key.pem",
            },
        ),
    )
