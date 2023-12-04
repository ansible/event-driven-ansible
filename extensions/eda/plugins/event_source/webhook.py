"""webhook.py.

An ansible-rulebook event source module for receiving events via a webhook.
The message must be a valid JSON object.

Arguments:
---------
    host:     The hostname to listen to. Defaults to 0.0.0.0 (all interfaces)
    port:     The TCP port to listen to.  Defaults to 5000
    token:    The optional authentication token expected from client
    certfile: The optional path to a certificate file to enable TLS support
    keyfile:  The optional path to a key file to be used together with certfile
    password: The optional password to be used when loading the certificate chain
    hmac_secret: The optional HMAC secret used to verify the payload from the client
    hmac_algo: The optional HMAC algorithm used to calculate the payload hash.
               See your python's hashlib.algorithms_available set for available options.
               Defaults to sha256
    hmac_header: The optional HMAC header sent by the client with the payload signature.
                 Defaults to x-hub-signature-256
    hmac_format: The optional HMAC signature format format.
                 Supported formats: hex, base64
                 Defaults to hex

"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import ssl
from collections.abc import Callable
from typing import Any

from aiohttp import web

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


def _parse_token(request: web.Request) -> (str, str):
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

    return hmac.compare_digest(hmac_header_digest, event_digest)


@web.middleware
async def bearer_auth(request: web.Request, handler: Callable) -> web.StreamResponse:
    """Verify authorization is Bearer type."""
    try:
        _parse_token(request)
    except KeyError:
        raise web.HTTPUnauthorized(reason="Missing authorization token") from None
    except ValueError:
        raise web.HTTPUnauthorized(text="Invalid authorization token") from None

    return await handler(request)


@web.middleware
async def hmac_verify(request: web.Request, handler: Callable) -> web.StreamResponse:
    """Verify event's HMAC signature."""
    hmac_verified = await _hmac_verify(request)
    if not hmac_verified:
        raise web.HTTPUnauthorized(text="HMAC verification failed")

    return await handler(request)


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
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

    context = None
    if "certfile" in args:
        certfile = args.get("certfile")
        keyfile = args.get("keyfile", None)
        password = args.get("password", None)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            context.load_cert_chain(certfile, keyfile, password)
        except Exception:
            logger.exception("Failed to load certificates. Check they are valid")
            raise

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        args.get("host") or "0.0.0.0",  # noqa: S104
        args.get("port"),
        ssl_context=context,
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

    class MockQueue:
        """A fake queue."""

        async def put(self: "MockQueue", event: dict) -> None:
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
