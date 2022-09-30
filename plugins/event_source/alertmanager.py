"""
alertmanager.py

An ansible-events event source module for receiving events via a webhook from
alertmanager.

Arguments:
    host: The hostname to listen to. Set to 0.0.0.0 to listen on all
          interfaces. Defaults to 127.0.0.1
    port: The TCP port to listen to.  Defaults to 5000

Example:

    - ansible.eda.alertmanager:
        host: 0.0.0.0
        port: 8000

"""

import asyncio
from typing import Any, Dict

from aiohttp import web
import dpath

routes = web.RouteTableDef()


@routes.get("/")
async def status(request: web.Request):
    return web.Response(status=200, text="up")


@routes.post("/{endpoint}")
async def webhook(request: web.Request):
    payload = (await request.json(),)
    endpoint = request.match_info["endpoint"]
    data = {
        "payload": payload,
        "meta": {"endpoint": endpoint, "headers": dict(request.headers)},
    }
    await request.app["queue"].put(data)

    for item in payload:
        for alert in item.get("alerts"):
            hosts = []
            try:
                host = dpath.util.get(alert, 'labels.instance', separator=".")
                host = clean_host(host)
                if host is not None:
                    hosts.append(host)
            except KeyError:
                pass

            await request.app["queue"].put(
                dict(
                    alert=alert,
                    meta=dict(endpoint=endpoint,
                              headers=dict(request.headers),
                              hosts=hosts),
                )
            )

    return web.Response(status=202, text="Received")


def clean_host(host):
    if ":" in host:
        return host.split(":")[0]
    else:
        return host


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    app = web.Application()
    app["queue"] = queue

    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,
                       args.get("host") or "localhost",
                       args.get("port") or 5000)
    await site.start()

    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {}))
