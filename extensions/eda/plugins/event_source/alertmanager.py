"""alertmanager.py.

An ansible-rulebook event source module for receiving events via a webhook from
alertmanager or alike system.

Arguments:
---------
    host: The webserver hostname to listen to. Set to 0.0.0.0 to listen on all
          interfaces. Defaults to 127.0.0.1
    port: The TCP port to listen to.  Defaults to 5000
    data_alerts_path: The json path to find alert data. Default to "alerts"
                      Use empty string "" to treat the whole payload data as
                      one alert.
    data_host_path: The json path inside the alert data to find alerting host.
                    Use empty string "" if there is no need to find host.
                    Default to  "labels.instance".
    data_path_separator: The separator to interpret data_host_path and
                         data_alerts_path. Default to "."
    skip_original_data: true/false. Default to false
                        true: put only alert data to the queue
                        false: put sequentially both the received original
                               data and each parsed alert item to the queue.

Example:
-------
    - ansible.eda.alertmanager:
        host: 0.0.0.0
        port: 8000
        data_alerts_path: alerts
        data_host_path: labels.instance
        data_path_separator: .

"""

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


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
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

    class MockQueue:
        """A fake queue."""

        async def put(self: "MockQueue", event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {}))
