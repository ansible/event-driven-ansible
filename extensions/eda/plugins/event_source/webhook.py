"""
webhook.py

An ansible-rulebook event source module for receiving events via a webhook.

Arguments:
    host:     The hostname to listen to. Set to 0.0.0.0 to listen on all
              interfaces. Defaults to 127.0.0.1
    port:     The TCP port to listen to.  Defaults to 5000
    token:    The optional authentication token expected from client
    certfile: The optional path to a certificate file to enable TLS support
    keyfile:  The optional path to a key file to be used together with certfile
    password: The optional password to be used when loading the certificate chain

"""

import asyncio
import logging
import ssl
from typing import Any, Callable, Dict

from aiohttp import web

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.post(r"/{endpoint:.*}")
async def webhook(request: web.Request):
    payload = await request.json()
    endpoint = request.match_info["endpoint"]
    headers = dict(request.headers)
    headers.pop("Authorization", None)
    data = {
        "payload": payload,
        "meta": {"endpoint": endpoint, "headers": headers},
    }
    await request.app["queue"].put(data)
    return web.Response(text=endpoint)


@web.middleware
async def bearer_auth(request: web.Request, handler: Callable):
    try:
        scheme, token = request.headers["Authorization"].strip().split(" ")
        if scheme != "Bearer":
            raise web.HTTPUnauthorized(text="Only Bearer type is accepted")
        elif token != request.app["token"]:
            raise web.HTTPUnauthorized(text="Invalid authorization token")
    except KeyError:
        raise web.HTTPUnauthorized(reason="Missing authorization token")
    except ValueError:
        raise web.HTTPUnauthorized(text="Invalid authorization token")

    return await handler(request)


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    if "port" not in args:
        raise ValueError("Missing required argument: port")
    if "token" in args:
        app = web.Application(middlewares=[bearer_auth])
        app["token"] = args["token"]
    else:
        app = web.Application()
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
            logger.error("Failed to load certificates. Check they are valid")
            raise

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        args.get("host") or "0.0.0.0",
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

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(
        main(
            MockQueue(),
            {
                "port": 2345,
                "token": "hello",
                "certfile": "cert.pem",
                "keyfile": "key.pem",
            },
        )
    )
