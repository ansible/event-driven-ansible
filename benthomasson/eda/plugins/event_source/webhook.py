"""
webhook.py

An ansible-events event source module for receiving events via a webhook.

Arguments:
    host: The hostname to listen to. Set to 0.0.0.0 to listen on all
          interfaces. Defaults to 127.0.0.1
    port: The TCP port to listen to.  Defaults to 5000

"""

import asyncio
from typing import Any, Dict

from aiohttp import web

routes = web.RouteTableDef()


@routes.post("/{endpoint}")
async def webhook(request: web.Request):
    payload = await request.json()
    endpoint = request.match_info["endpoint"]
    data = {
        "payload": payload,
        "meta": {"endpoint": endpoint, "headers": dict(request.headers)},
    }
    await request.app["queue"].put(data)
    return web.Response(text=endpoint)


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    app = web.Application()
    app["queue"] = queue

    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner, args.get("host") or "localhost", args.get("port") or 5000
    )
    await site.start()

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        print("Plugin Task Cancelled")
    finally:
        await runner.cleanup()


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {}))
