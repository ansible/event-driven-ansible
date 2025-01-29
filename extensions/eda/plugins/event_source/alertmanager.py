import asyncio
import logging
from typing import Any

from aiohttp import web
from dpath import util

routes = web.RouteTableDef()


@routes.get("/")
async def status(_request: web.Request) -> web.Response:
    """Return status of a web request."""
    return web.Response(status=200, text="up")


@routes.post("/{endpoint}")
async def webhook(request: web.Request) -> web.Response:
    """Read events from webhook."""
    payload = await request.json()
    endpoint = request.match_info["endpoint"]

    if not request.app["skip_original_data"]:
        data = {
            "payload": payload,
            "meta": {"endpoint": endpoint, "headers": dict(request.headers)},
        }
        await request.app["queue"].put(data)

    if not request.app["data_alerts_path"]:
        alerts = [payload]
    else:
        alerts = []
        try:
            alerts = util.get(
                payload,
                request.app["data_alerts_path"],
                separator=request.app["data_path_separator"],
            )
            if not isinstance(alerts, list):
                alerts = [alerts]
        except KeyError:
            # does not contain alerts
            pass

    for alert in alerts:
        hosts = []
        if request.app["data_host_path"]:
            try:
                host = util.get(
                    alert,
                    request.app["data_host_path"],
                    separator=request.app["data_path_separator"],
                )
                host = clean_host(host)
                if host is not None:
                    hosts.append(host)
            except KeyError:
                # does not contain hosts
                pass

        await request.app["queue"].put(
            {
                "alert": alert,
                "meta": {
                    "endpoint": endpoint,
                    "headers": dict(request.headers),
                    "hosts": hosts,
                },
            },
        )

    return web.Response(status=202, text="Received")


def clean_host(host: str) -> str:
    """Remove port from host string if it exists."""
    if ":" in host:
        return host.split(":")[0]
    return host


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via alertmanager webhook."""
    app = web.Application()
    app["queue"] = queue
    app["data_host_path"] = str(args.get("data_host_path", "labels.instance"))
    app["data_path_separator"] = str(args.get("data_path_separator", "."))
    app["data_alerts_path"] = str(args.get("data_alerts_path", "alerts"))
    app["skip_original_data"] = bool(args.get("skip_original_data", False))

    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.get("host", "localhost"), args.get("port", 5000))
    await site.start()

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logging.getLogger().info("Plugin Task Cancelled")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {}))
