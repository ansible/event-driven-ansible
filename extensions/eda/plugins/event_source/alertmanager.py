import asyncio
import hmac
import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from aiohttp import web
from dpath import util

DOCUMENTATION = r"""
---
short_description: Receive events via a webhook from alertmanager or a compatible alerting system.
description:
  - An ansible-rulebook event source module for receiving events via a webhook from alertmanager
    or a compatible alerting system.
options:
  host:
    description:
      - The webserver hostname to listen to. Set to 0.0.0.0 to listen on all
        interfaces.
    type: str
    default: "localhost"
  port:
    description:
      - The TCP port to listen to.
    type: int
    default: 5000
  data_alerts_path:
    description:
      - The json path to find alert data.
      - Use empty string "" to treat the whole payload data as one alert.
    type: str
    default: "alerts"
  data_host_path:
    description:
      - The json path inside the alert data to find alerting host.
      - Use empty string "" if there is no need to find host.
    type: str
    default: "labels.instance"
  data_path_separator:
    description:
      - The separator to interpret data_host_path and data_alerts_path.
    type: str
    default: "."
  skip_original_data:
    description:
      - >
        true: put only alert data to the queue
      - >
        false: put sequentially both the received original data and each parsed alert item to the queue.
    type: bool
    default: false
  token:
    description:
      - The optional bearer token expected in the Authorization header of
        webhook requests.
      - Set it in alertmanager with C(http_config.authorization.credentials)
        of the webhook receiver.
      - The status endpoint C(GET /) does not require the token.
    type: str
"""

EXAMPLES = r"""
- ansible.eda.alertmanager:
    host: 0.0.0.0
    port: 8000
    data_alerts_path: alerts
    data_host_path: labels.instance
    data_path_separator: .

- ansible.eda.alertmanager:
    host: 0.0.0.0
    port: 8000
    token: "{{ alertmanager_token }}"

# Matching alertmanager receiver
# receivers:
#   - name: eda
#     webhook_configs:
#       - url: http://eda.example.com:8000/endpoint
#         http_config:
#           authorization:
#             type: Bearer
#             credentials: <token>
"""


routes = web.RouteTableDef()


@routes.get("/")
async def status(_request: web.Request) -> web.Response:
    """Return status of a web request."""
    return web.Response(status=200, text="up")


def _event_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Copy request headers without the Authorization header, in any case."""
    return {k: v for k, v in headers.items() if k.lower() != "authorization"}


@routes.post("/{endpoint}")
async def webhook(request: web.Request) -> web.Response:
    """Read events from webhook."""
    payload = await request.json()
    endpoint = request.match_info["endpoint"]
    headers = _event_headers(request.headers)

    if not request.app["skip_original_data"]:
        data = {
            "payload": payload,
            "meta": {"endpoint": endpoint, "headers": headers},
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
                    "headers": headers,
                    "hosts": hosts,
                },
            },
        )

    return web.Response(status=202, text="Received")


@web.middleware
async def bearer_auth(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """Verify the Authorization header carries the expected bearer token."""
    if request.method == "GET" and request.path == "/":
        return await handler(request)

    scheme, _, token = request.headers.get("Authorization", "").strip().partition(" ")
    valid = hmac.compare_digest(token.strip().encode("utf-8"), request.app["token"])
    if scheme != "Bearer" or not valid:
        raise web.HTTPUnauthorized(text="Invalid authorization token")

    return await handler(request)


def clean_host(host: str) -> str:
    """Remove port from host string if it exists."""
    if ":" in host:
        return host.split(":", maxsplit=1)[0]
    return host


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via alertmanager webhook."""
    middlewares = []
    if args.get("token"):
        middlewares.append(bearer_auth)

    app = web.Application(middlewares=middlewares)
    app["queue"] = queue
    if args.get("token"):
        app["token"] = str(args["token"]).encode("utf-8")
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
